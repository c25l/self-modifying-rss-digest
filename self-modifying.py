import sys
import re
import feedparser
import smtplib
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


config = {"email_from": "",
        "email_to": "",
        "pass":"",
        "feeds":[]}
               
# this block will be rewritten every time because, you know, yolo. Don't touch it.
# ------- START -------
data = [{},{}]
# ------- END -------
class Bloom:
    def __init__(self):
        self.data = [{},{}]
    def __repr__(self):
        return str(self.data)
    def _hashes(self, other):
        carry = ""
        out = []
        for ii,_ in enumerate(self.data):
            hashed  = hashlib.md5(bytes(other+carry, 'utf-8')).hexdigest()
            out.append(int(hashed,16)%(2**20))
            carry += ":"
        return out
    def __add__(self, other):
        hashes = self._hashes(other)
        for ii, _ in enumerate(self.data):
            self.data[ii][hashes[ii]]=True
        return self
        
    def __getitem__(self, other):
        #returns whether or not it's unseen.
        hashes = self._hashes(other)
        maybe = True
        for ii, xx in enumerate(self.data):
            if hashes[ii] in xx:
                maybe = False
        return maybe
        
    def reset(self, data):
        self.data = data

class Feed:
    def __init__(self, feed):
        self.feed = feed
        self.items = []
        self.title = feed
    
    def parse(self):
        data =feedparser.parse(self.feed) 
        if 'feed' in data and 'title' in data.feed:
            self.title = data.feed.title
        self.items = ["<a href=" + y['link'] +">"+y['title']+"</a><br>\n" + y['summary'] + "\n<hr>\n" for y in data.entries]


    def unseen(self, bloom):
        self.parse()
        self.items = [z for z in self.items if bloom[z]]
        for xx in self.items:
            bloom += xx

    def html(self):
        outstr="<h2>"+self.title+"</h2><br>\n"
        for y in self.items:
                    outstr+= y
        outstr+="<hr>"
        return outstr

class Email:
    def __init__(self, e_to, e_from, e_pass):
        self.e_to = e_to
        self.e_from = e_from
        self.e_pass = e_pass
        self.server = 'smtp.gmail.com'
        self.port = 465
        self.text = ""

    def add_text(self, more):
        self.text += more

    def send(self):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Daily RSS rollup"
        msg['From'] = "\"RSS digest\" <"+self.e_from+">"
        msg['To'] = self.e_to
        text = "Hey, this is better as an html email!"
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(self.text, 'html')
        msg.attach(part1)
        msg.attach(part2)
        smtpObj = smtplib.SMTP_SSL(self.server, self.port)
        smtpObj.login(self.e_from, self.e_pass)
        smtpObj.sendmail(self.e_from, self.e_to, msg.as_string())  

def self_modify(new_data):
    data = []
    with open(sys.argv[0]) as file:
        for line in file:
            data.append(line)
    start = [x for x,y in enumerate([re.search(r'# -{7} START -{7}',x) for x in data]) if y][0]
    end = [x for x,y in enumerate([re.search(r'# -{7} END -{7}',x) for x in data]) if y][0]
    written = False
    with open(sys.argv[0], 'w') as file:
        for ii,line in enumerate(data):
            if ii<=start or ii>=end:
                file.write(line )
            if ii >= start and not written:
                written = True
                file.write(new_data+"\n")

def main():
    g= Bloom()
    g.reset(data)
    out = Email(config["email_to"], config["email_from"], config["pass"])
    out.add_text("<html><head></head><body>\n")
    for feed in config["feeds"]:
        feed = Feed(feed)
        feed.unseen(g)
        out.add_text(feed.html())
    out.add_text("</body></html>\n")
    out.send()
    self_modify("""data = {}""".format(str(g)))
    

if __name__ == "__main__":
    main()
