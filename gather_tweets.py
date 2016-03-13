import tweepy

CONSUMER_KEY = 'PttJa97W2j60SzWUAf88djOT1'
CONSUMER_SECRET = 'kSS4PTybZBGCOvMjRVM5bri0dZLEBwdZvX0DvQ3GlR19IagLfW'
ACCESS_KEY = '155832602-5dvQoe2EA1HDWcMFfECHRDDBcBL2U7LHSYSLYSOZ'
ACCESS_SECRET = 'KaqnTLEBDJGjTa3U5ZewrG4au3i7CzQX2KkW3QznOizjK'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

search_text = "#МЧС"
search_number = 100

cursor = tweepy.Cursor(api.search, search_text, count=search_number, lang='ru')

def preprocess(text):
    """Strip useless whitespaces and trailing \" from text.

    Args:
        text: String to preprocess.
    Returns:
        Processed text.
    """

    text = text.strip("\n \"\t").lstrip(".").replace('\n', '')

    return text
    
with open("tweets.csv", "w", encoding="utf-8") as f:
    head = "TweetID;Text;Author;Date"
    for result in cursor.items(limit=search_number):
        output_line = "%s;%s;%s;%s\n"%( result.id,preprocess(result.text), result.author.screen_name, result.created_at)
        f.write(str(output_line))