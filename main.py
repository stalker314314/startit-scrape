# Let's first start with defining imports to our scraper

# This is former urllib2 (in python 2.x) and we need it to talk to web sites (startit.rs in this case)
import urllib.request

# This is library to parse retrieved HTML content from web site
from bs4 import BeautifulSoup

# We only need this if we are going to persist scraped data somewhere, MongoDB in this case)
from pymongo import MongoClient

# Library to send mails (you need to be registered with Twilio and to get API keys to use it)
from twilio.rest import TwilioRestClient

# API keys for Twilio (not sharing mines:) - you need to add yours here
ACCOUNT_SID = "<twilio sid>" 
AUTH_TOKEN = "<twilio token>" 

# Definition of headers we need to make startit.rs accept our requests (we only need user agent)
user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'
headers={'User-Agent':user_agent}

if __name__ == '__main__':
    """ Main function (and only function) """
    # Let's first set up some basics - twilio client to send SMS and mongo client to access MongoDB
    twilio_client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 
    
    client = MongoClient()
    oglasi_coll = client.startit.oglasi # Our DB and collection where we put ads

    # Start with request to startit.rs/poslovi to get whole page
    request = urllib.request.Request('http://startit.rs/poslovi/', None, headers)
    # Actually do request
    response = urllib.request.urlopen(request)
    # and read response from web page (we do not check response nor we catch HTTPError if any)
    html_content = response.read()
    # Now let beautiful soup swallow that HTML and parse it for us
    soup = BeautifulSoup(html_content)
    
    # Now that we have parsed HTML, we can play whatever we want with it and extract all info we need
    # Let's iterate for all premium ads
    for oglas_soup in soup.select('div.listing-oglas-premium'):
        # oglas is simple dictionary variable which we will use later to insert into MongoDB.
        # At this point, we are just populating it with info we want.
        oglas = {}
        oglas['url'] = oglas_soup.find('a')['href']
        oglas['title'] = oglas_soup.select('div.listing-oglas-premium-text > h1 > a')[0].text
        oglas['company'] = oglas_soup.select('div.listing-oglas-premium-text > div.listing-ime-firme > a')[0].text
        oglas['tags'] = []
        for tags_soup in oglas_soup.select('div.listing-oglas-premium-text > small > a'):
            oglas['tags'].append(tags_soup.text)

        # Check with MongoDB whether this ad already exists
        # If it does, we do nothing, just skip it. If it doesn't - add it to DB and send SMS
        if oglasi_coll.find({'url': oglas['url']}).count() == 0:
            oglasi_coll.insert(oglas)
            twilio_client.messages.create(to="+381693141592", from_="+18474161102", body="Novi oglas - %s" % oglas['url'])