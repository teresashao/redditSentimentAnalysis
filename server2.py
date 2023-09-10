from flask import Flask, redirect, url_for, render_template, request, jsonify 

import praw 
import pandas as pd 
import nltk 
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from praw.models import MoreComments

app = Flask(__name__)

#for subreddit sentiment 
@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        subreddit_name = request.form["nm"] 
        return redirect(url_for("subreddit_sentiment", sr_name = subreddit_name))
    else:
        return render_template("login.html", sr_name = "hi", content = "SUBREDDIT SENTIMENT ANALYSIS", sentiment_mean = "", title1 = "5 MOST NEGATIVE HEADLINES", title2 = "5 MOST NEGATIVE HEADLINES",neg_headlines = [], pos_headlines = [], url_one = url_for("home"), url_two = url_for("comments"))

@app.route("/<sr_name>")
def subreddit_sentiment(sr_name):
    return get_titles_sentiment(sr_name)

def get_titles_sentiment(sr_name):
    user_agent = "Scraper 1.0"
    reddit = praw.Reddit(
    client_id = "57k9qkHywvTCMtPff9EFQQ",
    client_secret = "buDc1ptPFyyCrjt5uNNC-PwI70V2OA", 
    user_agent = user_agent
    )

    #ERROR PAGE IF SUBREDDIT DOESNT EXIST ????!!!!!

    titles = []
    titles_links = []

    #can use hot, new, rising, or top instead of hot 
    for submission in reddit.subreddit(sr_name).hot(limit=None):
        titles.append(submission.title)
        titles_links.append("https://www.reddit.com" + submission.permalink)

    analyzer = SentimentIntensityAnalyzer()     
    results_titles = []
    processed_titles = []
    link_idx = 0

    for line in titles:
        pol_score = analyzer.polarity_scores(line)
        pol_score['title'] = line
        pol_score['link'] = titles_links[link_idx]
    
        results_titles.append(pol_score) 
        processed_titles.append(line)
        link_idx = link_idx + 1

    compound_sum = 0
    #find the average sentiment score 
    for result in results_titles:
        compound_sum = compound_sum + result['compound']

    average = compound_sum/len(results_titles)

    #find top 5 headlines 
    for i in range(len(results_titles)):
        for j in range(i + 1, len(results_titles)):
            if results_titles[i]['compound'] > results_titles[j]['compound']:
                results_titles[i], results_titles[j]= results_titles[j], results_titles[i]
                titles_links[i], titles_links[j]= titles_links[j], titles_links[i]
                processed_titles[i], processed_titles[j]= processed_titles[j], processed_titles[i]

    five_neg_titles = processed_titles[0:5]
    five_neg_links = titles_links[0:5]
    neg_titles_links = []
    for i in range (len(five_neg_titles)):
        neg_titles_links.append([five_neg_links[i], five_neg_titles[i]])

    five_pos_titles = processed_titles[-5:]
    #five_pos_links = titles_links[-5:]

    sentiment_line_return = []
    
    sentiment_line_return.append(average)
    sentiment_line_return.append(five_neg_titles)
    #sentiment_line_return.append(five_neg_links)
    sentiment_line_return.append(five_pos_titles)
    #sentiment_line_return.append(five_pos_links)

    return render_template("login.html", content = "SUBREDDIT SENTIMENT ANALYSIS", sentiment_mean = average, title1 = "5 NEGATIVE HEADLINES", title2 = "5 POSITIVE HEADLINES", neg_headlines = five_neg_titles, pos_headlines = five_pos_titles, url_one = url_for("home"), url_two = url_for("comments"))#mean, a list of 5 neg titles, a list of 5 neg links, a list of 5 pos titles, a list of 5 pos links  

#COMMENTS SENTIMENT
@app.route("/comments", methods=["POST", "GET"])
def comments():
    if request.method == "POST":
        url = request.form["ur"] 
        print("REACHED!!")
        #replace reddit.com of url with "" blank and replace  
        url.replace("https://www.reddit.com/r/", "")
        #
        #
        #what if instead of passing in URL, we pass in an ID????!!!!!!!
        #
        #
        url.replace("/", "*")
        return redirect(url_for("c_c_c", mypath = url))
    else:
        return render_template("comments.html", post_url = "", content = "POST SENTIMENT ANALYSIS", neg_headlines = [], pos_headlines = [], url_one = url_for("home"), url_two = url_for("comments"))

def add_comments(comments_list, curr_comment):
    if isinstance(curr_comment, MoreComments): #unfold the MoreComments thing and move on to add the replies in MoreComemnts
        for c in curr_comment.comments():
            add_comments(comments_list, c)
    elif (len(curr_comment.replies) ==0 and type(curr_comment)!= 'MoreComments'): #there aren't more replies or comments to load
        return
    else:
        for comment in curr_comment.replies:
            if not isinstance(comment, MoreComments):
                comments_list.add(comment)
            add_comments(comments_list, comment)
    
@app.route("/<path:mypath>")
def c_c_c(mypath):
    print("REACHED2!!")
    user_agent = "Scraper 2.0"
    reddit = praw.Reddit(
    client_id = "57k9qkHywvTCMtPff9EFQQ",
    client_secret = "buDc1ptPFyyCrjt5uNNC-PwI70V2OA", 
    user_agent = user_agent
    )
    url = mypath

    #UNDO processing of url 
    url.replace("*", "/")
    url = "https://www.reddit.com/r/" + url
    # Creating a submission object
    submission = reddit.submission(url = url)
    post_comments = set()
    for comment in submission.comments:
        if not isinstance(comment, MoreComments):
            post_comments.add(comment)
        add_comments(post_comments, comment)

    #get rid of mods 
    for comment in post_comments.copy():
        print(comment.subreddit)
        try:
            if (comment.author.is_mod):
                print("REACHED")
                post_comments.remove(comment)
        except:
            continue

    return render_template("comments.html", content = "POST SENTIMENT ANALYSIS", sentiment_mean = get_comments_sentiment(post_comments), title1 = "", title2 = "", neg_headlines = [], pos_headlines = [], url_one = url_for("home"), url_two = url_for("comments"))


def get_comments_sentiment(post_comments):
    results = []
    compound_sum = 0
    compound_count = 0
    analyzer = SentimentIntensityAnalyzer() 
    for comment in post_comments:
        pol_score = analyzer.polarity_scores(comment.body)
        results.append(pol_score)
        compound_sum = compound_sum + pol_score['compound']
        compound_count = compound_count + 1
    
    return compound_sum/compound_count

if __name__ == '__main__':
    app.run(debug = True)

#add all da python sentiment code here!!