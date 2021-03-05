'''
Sample JSON output looks something like this:

{
    books: [
        {
            title: [
                {
                    word: jp,
                    defintion: eng,
                    reading: jp,
                    part_of_speech: eng,
                    sample_sent: from_kindle
                },
            ]
        },
        {
            title : [{}]
        },
    ]
}
'''
import sqlite3 # for reading vocab.db
import json # for creating json file
import requests # for getting definitions from jisho
import sys

JISHO_API = 'https://jisho.org/api/v1/search/words?keyword='
def create_json_from_db(db_file: str):
    # Connect to db
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    # Open the JSON file we'll write to
    with open('kindle_data.json', 'w+', encoding='utf-8') as f:
        # Setup the root of the json object
        json_head = {}
        # We will store different books as seperate arrays of words
        books = []
        json_head['books'] = books
        # Get all titles first
        c.execute('SELECT id, title FROM BOOK_INFO')
        id_titles = c.fetchall()
        # iterate through one book at a time.
        for ident, title in id_titles:
            # Setup an empty dict for the current book
            cur_book_data = {}
            books.append(cur_book_data)
            # Setup an empty array where we'll store word info later
            word_info = []
            cur_book_data[title] = word_info
            # Per documentation, using this format for the ident insertion when we execute our query
            ident_as_tuple = (ident,)
            # Use the query to ensure we get unique words in the event there have been
            # multiple lookups on the same word.
            # We pick the word with the shortest context
            query = '''
SELECT word_key, usage
FROM LOOKUPS l1
WHERE book_key=? AND NOT EXISTS (
	SELECT 1
	FROM LOOKUPS l2
	WHERE l1.word_key = l2.word_key and l1.usage < l2.usage
)
            '''
            c.execute(query, ident_as_tuple)
            results = c.fetchall()
            # Collect all the data to insert into the json file
            for result in results:
                word, usage = result
                # All words in the DB start with '<lang_key>:', but we don't need that
                # TODO: If we were making this multi-lang supporting, could pick a new
                # request source based on the split[0]
                word = word.split(':')[1]
                res = requests.get(JISHO_API + word)
                res_data = res.json().get('data', [])
                # Default definition, reading, part of speech to 'invalid' results
                # Anything processing the JSON can look for these specifically
                definition = 'NO DEFINITION FOUND'
                reading = 'NO READING FOUND'
                part_of_speech = ''
                # Parse out the dictionary data from the Jisho response
                if res_data:
                    res_data = res_data[0]
                    japanese = res_data.get('japanese', [])
                    if japanese:
                        reading = japanese[0].get('reading', 'NO READING FOUND')
                    senses = res_data.get('senses', [])
                    if senses:
                        senses = senses[0]
                        # Grab up to two definitions
                        defs = senses.get('english_definitions', [])
                        found_defs = []
                        for i in range(min(2, len(defs))):
                            found_defs.append(defs[i])
                        if found_defs:
                            definition = ', '.join(found_defs)
                        pos = senses.get('parts_of_speech', [])
                        part_of_speech = ', '.join(pos)
                # Implied else of no res data means we stick with default invalid definition/reading/part of speech

                # We now have all the data we need for our JSON. Create our dict
                cur_word_dict = {
                    'word' : word,
                    'definition': definition,
                    'reading': reading,
                    'part_of_speech': part_of_speech,
                    'sample': usage,
                }
                # Add this word to the word info for the current book
                word_info.append(cur_word_dict)
            # Finished getting information for the current words in the current book
            # print(str(word_info)) # <-- uncomment if you wish to see the results per book
        # End of loop going through every book in DB

        # Have finished collecting all our word information.
        # Write out to our json file now.
        f.write(json.dumps(json_head, indent=4))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('We require the path to the the SQLite3 vocab.db file')
        print('Connect your Kindle to your computer and do a search on it for \'vocab.db\' to find the location.')
        exit(1)
    db = sys.argv[1]
    create_json_from_db(db)
