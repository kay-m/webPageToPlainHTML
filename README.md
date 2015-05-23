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
# Usage:       The Script takes in two arguments
#               1. A text file containing list of article titles and their 
#                  respective URLs separated by an = symbol. 
#               2. Name of an output file. 

#              For URL in the list, the script extracts the paragraph elements 
#              in the web page and emits it as plain HTML to the output file. 
#              The titles are marked as HTML heading level 1
#              Text that is itallicized or in bold are maintained as is. All
#              other formatting elements are removed.
#-------------------------------------------------------------------------------

