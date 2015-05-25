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


# def convertToPlainHTML(urlDict):
# This is the workhorse method that does everything.

# Preconditions:
#  1. urlList is a list of tuples containing the URls to be processed. The
#     tuples are in the following format : (title,URL)
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
def convertToPlainHTML(urlList,outFileName):

  # Set logger to emit the name of the method for each msg from this method.
  logger = logging.getLogger(__name__)

  for item in urlList:

    # Remove the article Number Prefix added to the title
    title,URL = item[0],item[1]

    logger.info("Processing article - " + title)

    outStr = "<h1>" + title + "</h1>\n"

    # Its possible that some URLs are not accessible. If an error is
    # returned while accessing a URL, the page is skipped and execution
    # proceeds with the next URL in the list.

    try:
      page = requests.get(URL)
      page.encoding = 'utf-8'
      # Create a HTML document object
      tree = html.fromstring(page.text)
    except:
      logger.error("Error while accessing URL - " + URL)
      continue


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


    # Emit this only if it is different from the title.
    if (len(subtextTag) > 0 ) and \
       ( subtextTag[0].strip().upper() <> title.upper() ):

      outStr += "<h2>" + subtextTag[0].strip() + "</h2>\n"

    # Get all <p> nodes from document.

    pElemList = tree.xpath("//p")

    # Each element of of pElemList represents one <p></p> node.
    # node.getchildren() will return a list of all child nodes within the <p>
    # node. These could be <span>, <em>, <bold> or <br> elements.
    # node.iterText() will return an iterator that can used to get the text
    # within each node.

    endOfArticle = 0
    for pItem in pElemList:
      outStr += "<p>"
      # Add the <strong> and <em> tags back to the text.
      index = 0
      for child in pItem.getchildren():
        eTag = pItem.getchildren()[index].tag

        # eTag need not be a string always. Check for it
        if (isinstance(eTag, basestring)) and (eTag.upper() in ['EM','STRONG']):
          eTagOpen = "<" + eTag + ">"
          eTagClose = "</" + eTag + ">"

          if (pItem.getchildren()[index].text is not None) and \
              len(pItem.getchildren()[index].text.strip()) > 0:
            pItem.getchildren()[index].text = eTagOpen + \
                                              pItem.getchildren()[index].text + \
                                              eTagClose
          ''' Commenting this out for now. The tail thing is not working as
          # expected
          # It could also be a case where there are sub tags within a <em> or
          # <strong tag>. Am handling only one level of nesting since it seems
          # realistic at this point.
          # Child nodes of the em/strong tag =
          #                      pItem.getchildren()[index].getchildren()

          for ix in range(len(pItem.getchildren()[index].getchildren())):
            if pItem.getchildren()[index].getchildren()[ix].text is not None:
              pItem.getchildren()[index].getchildren()[ix].text = \
                eTagOpen + \
                pItem.getchildren()[index].getchildren()[ix].text + \
                eTagClose


          # Finally at to the trailing text portin of the original <em>
          # <strong> tag - <strong> blah blah <em> he he </em> goodbye </strong>
          # This is for the adding the strong tag for the text goodbye in the
          # above example.
          if pItem.getchildren()[index].tail is not None:
              pItem.getchildren()[index].tail = eTagOpen + \
                                              pItem.getchildren()[index].tail + \
                                              eTagClose
         '''
        # remove content inside script nodes
        if (isinstance(eTag, basestring)) and (eTag.upper() == 'SCRIPT'):
          pItem.getchildren()[index].text = ""

        # One more crazy thing to check for. There are some places where a <br/>
        # element is used in the middle of a paragraph to emit a line break.
        # As of now, I am emitting it as is. Ideally, I would like to correct it
        # by ending the paragraph element at that point and starting a new
        # paragraph from that point onward.
        if (isinstance(eTag, basestring)) and (eTag.upper() == 'BR'):
          pItem.getchildren()[index].text = "</br>"

        index = index + 1
      # end of loop

      # Combine the text within each child node.

      for txt in pItem.itertext():
        # Check for embedded java script code that masks the radiosai email id:
        # Some articles end with a note asking readers to write to
        # h2h@radiosai.org. This email id is wrapped inside javascript code that
        # is also emitted.
        if len(txt.strip()) > 0:
          if txt.startswith(u'Dear Reader, did this article'):
            txt = "Dear Reader, did this article inspire you in any way?" \
                  " Would you like to share you feelings with us? "\
                  " Please write to us  at h2h@radiosai.org "
            endOfArticle = 1

          if (endOfArticle == 1):
            uStr = u'[email\xa0protected]'
            txt = txt.replace(uStr,"")
            # remove a length piece of comment. Though this is not in final
            # output, its dirty junk!
            if txt.startswith("\n/*"):
              txt = ""

          outStr = outStr + txt

      outStr = outStr + "</p>\n"


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

  #Write out the training </body> and </html> tags
  with open(outFileName,mode="a") as file:
    file.write("\n</body></html>")
    file.close()

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
# b. Parse the cvs file and convert its contents into a list of tuples of the
#    form : (title,URL)
# c. Log file named WebPageToHTML.log is initialized.

if __name__ == '__main__':

    if len(sys.argv) <> 3:
      print "Error : File containing URL list or name of outut file is not " \
            "provided.\n" \
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

    # Convert CSV file to a list of tuples of the form (title,url).
    urlList = []
    try:
      articleNum = 0
      for line in open(sys.argv[1]).readlines():
        line = line.strip().split("=")
        if len(line[0].strip()) > 0 and len(line[1].strip())>0:
          tup = (line[0].strip(),line[1].strip())
          urlList.append(tup)
    except:
        print "Error while opening/processing the URL List file. \n"
        sys.exit()


    # Log number of elements in dictionary
    logger.info("Number of entries in URL File = "+str(len(urlList)))

    # truncate the contents of output file, if it exists.
    # Add the opening <HTML> and <BODY> tags
    try:
      with open(outFileName,"w") as file:
        str = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'\
              '<html> \n <head>' \
              '<title> compilation of Articles from media.radiosai.org '\
              '</title> \n </head> \n <body>'
        file.write(str)
        file.close()
    except:
      pass

    # Call the workhorse method for conversion.
    convertToPlainHTML(urlList,outFileName)
