import re
import sys
import getopt 
import os
import json
import re
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired

_debug = False
stderr_set = False

terminator =  ".[[[___]]]"
terminator_for_parsing = "[[[___]]]"

bad_words = []
good_words = []

out_emotional_treshold = 0.25
def pdebug(*args):
    """Write debug info to debug.txt if debug mode is on.

    Args:
        *args: sequence of strings to output.
    """
    if _debug:
        global stderr_set
        if not stderr_set:
            sys.stderr = open(os.path.dirname(os.path.abspath(__file__))+'\\debug.txt', 'w',encoding="utf-8")
            stderr_set = True

        print(" ".join(args),file=sys.stderr)

def read_emotion_collections():
    tesaurus_path = 'WordNetAffectEngRomRus/'
    good_files = ['joy', 'surprise']
    bad_files = ['fear','anger', 'sadness', 'disgust']

    good_words = []
    bad_words = []
    #word_search_pattern = re.compile(ur'(?u)\w+', re.U)
    word_search_pattern = re.compile(u"[\u0400-\u0500]+")

    for good in good_files:
        with open(tesaurus_path+good+'.txt', 'r', encoding='utf-8') as f:
            for line in f:
                good_words = good_words + word_search_pattern.findall(line)

    for bad in bad_files:
        with open(tesaurus_path+bad+'.txt', 'r', encoding='utf-8') as f:
            for line in f:
                bad_words = bad_words + word_search_pattern.findall(line)
    return bad_words, good_words

class NewsMessage():
    """A structure to hold information extracted from input and grammemes after parsing."""
    def __init__(self, id, text, author, date):
        self.id = id
        self.text = text
        self.date = date
        self.author = author
        self.grammemes = []
        self.sentiment = None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s;%s;%s;%s;%s"%(self.id, self.text, self.author, self.date, self.sentiment)

def preprocess(text):
    """Strip useless whitespaces and trailing \" from text.
        Remove all urls from text.
    Args:
        text: String to preprocess.
    Returns:
        Processed text.
    """

    
    text = text.strip("\n \"\t").lstrip(".").replace('\n', '')
    #text = re.sub(r'https?:\/\/.*[\r\n]*', '', text)
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    return text

def read_input(fname):
    """Read the input file line by line.

    Args:
        fname: filename to read
    Returns:
        List of NewsMessage objects.

    """
    news_objects = []
    with open(fname, "r", encoding="utf-8-sig") as f:
        for line in f:
            #pdebug("Parsing line\n", line,"\n[[[[[==============]]]]]\n")
            atrib = [x.strip("\"").strip() for x in line.split(';')]
            news_line = NewsMessage(atrib[0], atrib[1], atrib[2], atrib[3])
            news_line.text = preprocess(news_line.text)
            #news_line.grammemes = get_grammemes(news_line.text)
            news_objects.append(news_line)
            #pdebug("[[[[[==============]]]]]")
    return news_objects

def decompile_huge_strs(tomita_output_chunks):
    #Now that we have a list of processed huge chunks we have to:
    #1. Break each chunk into separate texts (e.g. ["a[[[___]]]b[[[___]]]c"] to [ ["a", "b", "c"] ])
    lists_of_texts = [stdout_data.split(terminator_for_parsing) for stdout_data in tomita_output_chunks]
    #2. Unpack all lists of texts into one list (e.g. [ ["a", "b", "c"] ] to ["a", "b", "c"])
    huge_list = [ ] #Each i-th text in 'huge_list' is a processed i-th text in 'texts' (and a processed text of i-th news message)
    for l in lists_of_texts:
        for text in l:
                huge_list.append(text)
    return huge_list
def compile_huge_strs(texts, huge_str_size=250):
    """Create a list of concated strings with a total of huge_str_size in each chunk to pass to tomita for processing
    Args:
        texts: list of texts to compile into huge strings.
    Returns:
        A list of huge strings made of texts separated by a special terminator.
    """
    huge_strs=[]
    cur_pos = 0
    num = huge_str_size
    #for num in range(huge_str_size, len(texts), huge_str_size):
    while cur_pos <= len(texts):
        huge_strs.append(terminator.join([text for text in texts[cur_pos:num]]))
        cur_pos = num
        num = cur_pos + huge_str_size

    #for text in texts:
        #huge_str += text + terminator
    return huge_strs


def post_process_tomita_facts(facts):
    """Remove duplicates and lowercase all facts

    Args:
        facts: dictionary of of format {'fact_type': [fact1, fact2 ... factn] }
    """
    for key in facts.keys():
        facts[key] = list(set([ x.lower() for x in facts[key] ]))
    return facts

def tomita_parse(text):
    try:
        p = Popen(['tomita/tomitaparser.exe', "tomita/config.proto"], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout_data, stderr_data = p.communicate(input=bytes(text, 'UTF-8'), timeout=300)
        stderr_data = stderr_data.decode("utf-8").strip()
        stdout_data = stdout_data.decode("utf-8").strip()
        print("Tomita returned:", stderr_data.replace("\n", ''))
        pdebug("Tomita returned stderr:\n", stderr_data+"\n" )
    except TimeoutExpired:
        p.kill()
        pdebug("Tomita killed due to timeout")
        print("Tomita killed due to timeout")

    return stdout_data, stderr_data

def parse_tomita_output(text):
    """Parse tomita text output to extract fact types and facts.

    Args:
        text: String to parse.

    Returns:
        Dictionary of format {'fact_type': [fact1, fact2 ... factn] }
    """
    facts = {}
    clearing_text = str(text)
    while clearing_text.find("{") != -1:
        opening_brace = clearing_text.find("{")
        if not opening_brace:
            break
        closing_brace = clearing_text.find("}", opening_brace)
        if not closing_brace:
            break
        fact_type=re.search('(\w+\s+)(?=\s+\{)', clearing_text[:closing_brace])
        if not fact_type:
            continue
        fact_type = fact_type.group(0).strip()
        fact_body = clearing_text[opening_brace-1:closing_brace+1]
        fact_text = fact_body[fact_body.find('=')+1:-1].strip()
        if not fact_type in facts.keys():
            facts[fact_type] = []
        facts[fact_type].append(fact_text)
        clearing_text = clearing_text.replace(fact_body, '')
    return post_process_tomita_facts(facts)

def extract_facts(news):
    """ Compile all texts into chunks of 50..250, send them to tomita for parsing, 
        put facts into NewsMessage objects. 

    Args:
        news: list on NewsMessage objects.
    Returns:
        List of NewsMessage objects.
    """
    texts = [news_line.text for news_line in news]
    text_per_chunk = min(max(int(len(texts)/20), 30), 250)
    print("Compiling texts into chunks with %d texts in each"%(text_per_chunk))
    huge_strs = compile_huge_strs(texts, text_per_chunk)
    #Pass huge str to tomita
    facts = []
    tomita_output_chunks = []
    pdebug("Sending huge str to tomita")
    total_huge_strs = len(huge_strs)
    for i in range(total_huge_strs):
        huge_str = huge_strs[i]
        print("Processing chunk %d/%d"%(i, total_huge_strs) )
        stdout_data, stderr_data = tomita_parse(huge_str)

        if i==0:
            pdebug("First huge chunk:\n/////HUGE CHUNK/////\n %s \n/////HUGE CHUNK/////\n"%(huge_str))
            pdebug("First huge chunk parsed:\n/////HUGE CHUNK PARSED/////\n %s \n/////HUGE CHUNK PARSED/////\n"%(stdout_data))

        tomita_output_chunks.append(stdout_data)

    
    huge_list = decompile_huge_strs(tomita_output_chunks)

    #pdebug("Hugelist sample, first text:\n", '\n'.join(huge_list[1]))
    pdebug("Total chunks %d, decompiled texts %d"%(total_huge_strs, len(huge_list)) )
    percentage = max(int(len(huge_list)*0.1), 1)
    for i in range(len(huge_list)):
        if i % percentage == 0:
            print("Parsing tomita output %d/%d"%(i, len(huge_list)) )
        text = huge_list[i]
        facts.append(parse_tomita_output(text))

    try:
        for i in range(len(texts)):
            pdebug("For text:\n%s\nReceived facts are:\n%s"%(texts[i], str(facts[i])))
            news[i].grammemes = facts[i]
    except:
        print('news:%d, texts originally:%d, texts after parsing: %d, facts:%d, i%d'%( len(news), len(texts), len(huge_list), len(facts), i ) )
    #launch tomita
    #read tomita output from stdout
    return news 

def analyze_sentiment(news):
    global good_words
    global bad_words
    for news_line in news:
        pdebug('Analyzing sentiment for newsline ' + news_line.id)
        bad = 0
        good = 0
        neutral = 0
        for key in news_line.grammemes.keys():
            if key != "EntityName":
                for word in news_line.grammemes[key]:
                    pdebug('Analyzing word '+ word)
                    if word in bad_words:
                        pdebug('bad')
                        bad += 1
                    elif word in good_words:
                        pdebug('good')
                        good += 1
                    else:
                        pdebug('neutral')
                        neutral += 1
        if good or bad or neutral:
            news_line.sentiment = (good - bad)/(good+bad+neutral*0.2)
        else:
             news_line.sentiment = 0
        pdebug('done\n')
    return news

def output(news, output_fname):
    with open(output_fname, 'w', encoding='utf-8') as f:
        f.write("ID;Text;Author;Date;Sentiment\n")#Table header
        for n in news:
            if abs(n.sentiment) >= out_emotional_treshold:
                f.write(str(n)+'\n')


def main(argv):
    input_fname = "tweets.csv"
    output_fname = "output.csv"
    try:                                
        opts, args = getopt.getopt(argv, "di:o:", ["input=", "output="])
    except getopt.GetoptError:
        print('todo help')
        sys.exit(2)   

    for opt, arg in opts:                                           
        if opt in ("-i", "--input"):
            input_fname = arg   
        elif opt in ("-o", "--output"):
            output_fname = arg
        elif opt == '-d':
            global _debug
            _debug = True
    
    print("Input file, output file:", input_fname, output_fname)
    global good_words, bad_words
    bad_words, good_words = read_emotion_collections()
    pdebug('Bad words:')
    pdebug(str(bad_words))
    pdebug('Good words:')
    pdebug(str(good_words))
    print("Reading input file...")
    news = read_input(input_fname)
    print("Done.")
    print("Extracting facts from text...")
    news = extract_facts(news)
    print('Analyzing sentiments')
    news = analyze_sentiment(news)
    print('Outputting results')
    output(news, output_fname)
    print("Done.")

if __name__ == "__main__":
    main(sys.argv[1:])