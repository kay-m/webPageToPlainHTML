#-------------------------------------------------------------------------------
# Purpose:     The purpose of the script is to convert the articles from the
#              articles archive at media.RadioSai.org into HTML text that is
#              ready for conversion to epub format using Calibre.
#
# Author:      Krishnamoorthy
#
# Created:     21/05/2015
# Copyright:   (c) Krishnamoorthy 2015
# Licence:     Free to use/modify as you wish.
# Usage:       The Script takes in a text file containing a comma separated list
#              of article titles and their respective URLs. It converts the
#              paragraph elements in the web page into plain HTML and emits a
#              HTML file as output.
#              The titles are marked as HTML heading level 1
#              Text that is itallicized or in bold are maintained as is. All
#              other formatting elements are removed.
#-------------------------------------------------------------------------------


#Convert HTML page to HTML document object
from lxml import html
import requests

# To handle writing unicode data to output file
import codecs
import unicodedata

import logging
import sys

# treeHasParaStartingWith(tree,st):
# Helper routine to determine is a given string is the beginning of a
# paragraph. This is needed because the xpath function used in
# convertToPlainHTML() routine below extracts any sub-tag within the <p>
# element as a separate item. Examples include content within <strong>
# and <em> tags. We need a way to merge these elements back together.
# The other option is to use a regex matcher. I am sticking with this
# approach for now.

# Preconditions :
#   Param tree points to an XML tree that contains all of the content
#   of the web page.
#   st is a non empty string.
# Return Value:
#     1 - If page contains a paragraph element starting with the string st
#     0 - otherwise

def treeHasParaStartingWith(tree,st):

  # xpath returns an exception for some strings. While these are eventually
  # written out to the output file, the strings that cause the exception are
  # logged. The exception may be due to unacceptable unicode characters.

  try:

    param = "//p[starts-with(text(),"
    param += "'" + st + "'"
    param += ")]/text()"

    # Extract all <p> elements that start with the string st
    elem = tree.xpath(param)

    #This is the only way to check that there was a match.
    if len(elem) > 0:
      return 1
    else:
      #check if it is nestled inside a <strong> tag
      param = "//p/strong[starts-with(text(),"
      param += "'" + st + "'"
      param += ")]/text()"

      elem = tree.xpath(param)
      if len(elem) > 0:
        return 1
      # There is no match for a paragraph starting with st.
      else:
        return 0
  except:
      logger.warning("Processing param failed. " + param)





# def isEnclosedInAttrs(tree,st):
# Helper routine to determine if string represented by param st is enclosed in
# specific tags in the web page. The specific tag to look for is specified by
# the third attribute - attr. This method is needed to re-insert these tags in
# the final output.

# Preconditions :
#   Param tree points to an XML tree that contains all of the content
#   of the web page.
#   st is a non empty string.
#   attr is one of the following values - "em", "strong" (this is not vaidated)

# Return Value:
#     1 - If page contains a attr element nested within a <p> element
#         starting with the string st
#     0 - otherwise

def isEnclosedInAttrs(tree,st,attr):

  # xpath may return an exception for some strings. I have not figured out the
  # reason for this. These strings will be emitted to the final output though.
  # Strings that cause an exception will be logged. Its possible that the
  # exception is due to unacceptable unicode characters.
  try:
    param = "//p/"
    param += attr.strip()
    param += "[starts-with(text(),"
    param += "'" + st + "'"
    param += ")]/text()"

    elem = tree.xpath(param)
    if len(elem) > 0:
      return 1
    else:
      return 0
  except:
    logger.warning("Processing param failed. " + param)


# def convertToPlainHTML(urlDict):
# This is the workhorse method that does everything.

# Preconditions:
#  1. urlDict is a dictionary containing the list of URls to be processed. The
#     keys are article titles.
#  2. outFileName is a valid file name to be used for the output file.

# Postconditions:
#  1. World peace, energy sufficiency and an Utopian society.
#  2. If 1 is not sufficient, the method also ensures the following:
#     For each item in the dictionary:
#       a. Extract the page specfied and convert it into a HTML document object
#       b. Extract the contents within all <p> nodes inluding content of child
#          nodes of a <p> node. (example - <strong>, <em> etc)
#  3. Errors/Warnings if any, are logged to a log file named
#     webPageToPlainHTML.log
#
def convertToPlainHTML(urlDict,outFileName):

  # Set logger to emit the name of the method for each msg from this method.
  logger = logging.getLogger(__name__)

  for title in urlDict.keys():

    logger.info("Processing article - " + title)

    outStr = "<h1>" + title + "</h1>\n"
    page = requests.get(urlDict[title])

    # Create a HTML document object
    tree = html.fromstring(page.text)

    # Extract Article title subtext Based on an inspection of a few of the
    # articles in the radio sai archive, I see that article subtext is usually
    # tagged with the class paraboldteal ot ArticleBlueHeader. If there are
    # more, they should be added to the list below.
    # A note on xpath parameter:
    # //p => a paragraph node in the document (puritans, please ignore this)
    # [@class = 'paraboldteal' => Paragraph node has attr named calss having
    #                             value paraboldteal
    #/text() > Get the text within this node.
    subtextTag = tree.xpath("//p[@class='paraboldteal']/text()|"\
                            "//p/strong[@class='ArticleBlueHeader']/text()")

    if len(subtextTag) > 0:
      outStr += "<h2>" + subtextTag[0] + "</h2>\n"

    # I had originally tried to extract selective <p> tags based on its class
    # attribute. I had to drop this since the articles did not maintain a
    # consistency of these class attributes. This lead to some content being
    # missed out. The drawback of the current approach is that some stray
    # may also get in. I am ok with that. The "descendant-or-self::text()"
    # param in the xpath paramater ensures that content of child nodes of
    # the <p> element are also extracted.

    #paragraphTags = tree.xpath("//p[@class='para' or @class='articlemaintext14' or
    #                                @class='articlemaintextbold14' or
    #                                @class='paraboldteal14' or
    #                                @class='paraboldteal14pt']"
    #                                 /descendant-or-self::text() |
    #                                 //p/strong[@class='articlemaintext14']
    #                                 /descendant-or-self::text()")


    paragraphTags = tree.xpath("//p/descendant-or-self::text() | "\
                               "//p/strong[@class='articlemaintext14'] "\
                               "/descendant-or-self::text()")

    # paragraphTags is a list of strings. Each element represents the content
    # inside a <p> or <p>/<strong> element.

    # Merge the list items such that all text corresponding to one paragraph
    # are in one element. I check if each element of the list is the starting
    # text for a <p> element. If yes, leave it alone. If not, the element
    # represents text inside a <strong> or <em> element. Mark these for
    # removal.

    removeElements = [] # Will hold indexes of elements to be removed.

    lastSeenParaIndex = -1 #Index of last seen element that begins a paragraph.

    for i in range(len(paragraphTags)):
      if (treeHasParaStartingWith(tree,paragraphTags[i]) == 0):
          removeElements.append(i)

          if lastSeenParaIndex > -1:
            # Check of element is withing <stron> or <em> elements. If yes,
            # add those tags to retain formatting.
            if (isEnclosedInAttrs(tree,paragraphTags[i],"strong")):
              paragraphTags[lastSeenParaIndex] += " <strong> " + \
                                                   paragraphTags[i] + \
                                                   "</strong>"
            else:
              if (isEnclosedInAttrs(tree,paragraphTags[i],"em ")):
                paragraphTags[lastSeenParaIndex] += " <em>" + \
                                                    paragraphTags[i] + \
                                                    "</em>"
              else:
                paragraphTags[lastSeenParaIndex] += " " + paragraphTags[i]
      else:
          lastSeenParaIndex = i

    # Create a new list  =
    # paragraphTags - list of items to be removed since they have been merged
    #                 with other elements
    paragraphList = []
    for i in range(len(paragraphTags)):
      if i not in removeElements:
        if (isEnclosedInAttrs(tree,paragraphTags[i],"strong")):
          paragraphList.append("<strong>" + paragraphTags[i] + "</strong>")
        else:
          paragraphList.append(paragraphTags[i])

    del paragraphTags # This list is not needed anymore
    del removeElements


   # There is one last piece of trickery that is needed. Some articles end with
   # a note asking readers to write to h2h@radiosai.org. The email id is wrapped
   # inside javascript code that is also emitted. The following piece of code
   # identifies this scenario and replaces with a template line.
   # Should improve this to read from end of list
    endOfArticleIndex = 0
    for i in range(len(paragraphList)):
      paragraphList[i] = paragraphList[i].strip()
      if paragraphList[i].startswith(u'Dear Reader, did this article'):
        paragraphList[i] = "Dear Reader, did this article inspire you in any way?" \
                           " Would you like to share you feelings with us? "\
                           " Please write to us  at h2h@radiosai.org."
        endOfArticleIndex = i
      if len(paragraphList[i]) > 0:
        outStr += "<p>" + paragraphList[i] + "</p>\n"

      if endOfArticleIndex > 0:
        break

    #Create outfile and write to it.
    # The content read is usually in iso-8859-1 encoding. Opening a file the
    # normal way leads to errors when there are some unicode characters. Hence
    # the use of the codecs module. I am also replacing unicode single and
    # double quotes with regulat quotes.

    outFile = codecs.open(outFileName,mode="a", encoding="iso-8859-1")

    outStr = outStr.replace(u"\u2018", "'")\
                   .replace(u"\u2019", "'")\
                   .replace(u"\u201c",'"')\
                   .replace(u"\u201d",'"')

    outStr = unicodedata.normalize('NFKC',outStr).encode('ascii','ignore')
    outFile.write(outStr)
    outFile.close()


# Strting point for the script.
# Preconditions :
#   1. Script is called with two additional parameters. The first parameter is
#      the name the file contining the list of URLs to be processed. Each entry
#      in the file is in the following format:
#      article-title = URL  (The = sign is the separator).
#   2. No two entries in the file have the same value for the article title.
#   3. The second parameter is the name of the output file to be generated.
#

# Postconditions:
#  1. The output file (name as specified in the command line - param 2) has
#     the content of all the articles listed in the URL List file in plain HTML.
#  2. If the file exists, its contents will be overwritten.
#  3. The tag for each article title will be HTML heading level 1 - <h1>

# The following piece of code does the following:
# a. Check that the command line arguments include a file containing the URLS
# b. Parse the cvs file and convert its contents to a dictionary. The keys of
#    of the dictionary are the article titles specified by the user. This
#    implies that no two articles can have the same title. If it does repeat, a
#    message is returned to the suer while processing continues on the remaining
#    links including the first one of the duplicates.
# c. Log file named WebPageToHTML.log is initialized.

if __name__ == '__main__':

    if len(sys.argv) <> 3:
      print "Error : File containing URL list is not provided.\n" \
            "Usage : python webPageToPlainHTML.py file-name-with-urls " \
            "output-file-name\n"

      sys.exit()

    outFileName = sys.argv[2]

    # truncate log file
    try:
      with open("webPageToPlainHTML.log") as file:
        pass
    except:
        pass


    # setup logger
    # INitialize logger to emit the filename, line number and function name
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"

    logging.basicConfig(filename='webPageToHTML.log', \
                        level=logging.INFO,format=FORMAT)
    logger = logging.getLogger(__name__)


    logger.info("Processing URL list file " + sys.argv[1])

    # Convert CSV file to a dictionary object.
    urlDict = {}
    try:
      for line in open(sys.argv[1]).readlines():
        line = line.strip().split("=")
        if len(line[0]) > 0 and len(line[1])>0:
          if line[0] not in urlDict.keys():
            urlDict[line[0].strip()] = line[1].strip()
          else:
            print "Title is repeating for two different URLs. Please use unique "\
                  " titles for each URL. Only the first occurence is being " \
                  " processed.\n" \
                  + "Title - " + line[0] \
                  + "URL 1 - " + urlDict[line[0]] + "\n" \
                  + "URL 2 - " + line[1]
    except:
        print "Error while opening/processing the URL List file. \n"
        sys.exit()


    # Log number of elements in dictionary
    logger.info("Number of entries in URL File = "+str(len(urlDict.keys())))

    # truncate the contents of output file, if it exists:
    try:
      with open(outFileName,"w") as file:
        file.close()
    except:
      pass

    # Call the workhorse method for conversion.
    convertToPlainHTML(urlDict,outFileName)
