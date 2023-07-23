# Clarifying Questions in Math Information Retrieval
This repository provides the data and the code for ICTIR'23 paper Clarifying Questions in Math Information Retrieval.
In this paper, clarifying questions on Math Stack Exchange (MathSE) have been extracted and analyzed.

## Data source
To get the raw MathSE data, we used the [Internet Archive](https://archive.org/). All the files are 
in XML format.

## Extraction
As explained in the paper, there are three approaches used to extract clarifying questions:
* CF:  Comments that are the first to be posted on the question
* CBA: Comments written before a comment posted by asker
* CMA: Comments that contain a mention of the asker

To extract the clarifying question from MathSE, use ``ExtractingCQs.py`` file. On the top of this file the path for 
XML files should be specified. You need the following files:
* Posts.xml
* Comments.xml
* Users.xml
* Badges.xml

The generated TSV file `MathCQs.tsv` has the following data:

  PostID CommentID QuestionTitle Comment AnswerStatus IsReplied Response ResponseTime
 
 The Comment is the clarifying question, and AnswerStatus has values 0: the question has at least one answer, -1: there are no
 answers to the question, and 1: there is an accepted answer to the question.
 
 **Note**  that in the available TSV files instead of CF we have used A, B for CBA, and C for CMA. 
