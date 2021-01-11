import shelve
from datetime import date
import threading

from flask import Flask
from feedgen.feed import FeedGenerator
from summerise import page_content_for_url

def makefeed():
    fg = FeedGenerator()
    fg.id('youtube')
    fg.title('YouTube conf feed')
    fg.author( {'name':'Thomas Parks'} )
    fg.link( href='http://localhost:5678/youtube.atom', rel='self' )
    fg.language('en')
    return fg

def render(item):
    """takes a db item and generates the page from it.
    mostly formatting code.
    """
    content, metadata = item["content"], item["metadata"]
    
    page = ""
    for timestamp, item in content:
        page += item.render()
    
    return page

def update_feed(item, fg):
    content, metadata = item["content"], item["metadata"]
    fe = fg.add_entry() # feed entry
    fe.id(metadata["webpage_url"])
    fe.title(metadata["title"])
    # upload_date_string = metadata["upload_date"]
    # upload_date = date.fromisocalendar(int(upload_date_string[0:4]), 
    #                                    int(upload_date_string[5:6]), 
    #                                    int(upload_date_string[7:]))
    # fe.published(upload_date)
    fe.link(href=metadata["webpage_url"])
    fe.content(content=render(item), type="html")
    # fe.author(metadata["uploader"])


def run_repl_interface(db, fg):
    while True:
        print("\n")
        cmd = input("> ")
        if cmd.split(" ")[0] == "add":
            url = cmd.split(" ")[1]
            if url in db.keys():
                if input("video present in db, replace (y/n)?") != "y":
                    continue
            else:
                try:
                    content, metadata = page_content_for_url(url)
                except Exception as e:
                    print(e)
                else:
                    db[url] = {"content":content, "metadata":metadata}
                    update_feed(db[url], fg)
                    db.sync()
        elif cmd == "quit":
            break
        else:
            print("error")
                
### Flask
app = Flask(__name__)
print("flask app created")

fg = makefeed()

@app.route('/youtube.atom')
def feed():
    return fg.atom_str(pretty=True) # Get the ATOM feed as string

with shelve.open("videos.db", writeback=True) as db:
    for key, page in db.items():
        update_feed(page, fg)
    print("feed updated from db")
    server = threading.Thread(target=app.run, kwargs={"use_reloader":False, "port":5678})
    server.start()
    print("server started")
    run_repl_interface(db, fg)
    server.stop()