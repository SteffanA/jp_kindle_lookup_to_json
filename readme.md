A small script used to parse the lookups from the built-in Kindle database and create JSON data that can be used to create flashcards programatically.

You can find the Kindle's built in lookup database sqllite3 file by plugging your kindle into a PC and searching for "vocab.db".


Currently only supports Japanese books/lookups into English definitions.


Output includes:
   > Word
   > Reading (in hirigana)
   > Definition (in English)
   > Part of Speech
   > Sample Usage (context around the looked-up word)


The output is provided in "kindle_data.json" when the program finishes.


The definition/part of speech/reading data are courtesy of Jisho.org
