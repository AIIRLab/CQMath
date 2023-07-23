# This code extract the clarifying questions from Math Stack Exchange
# The generated TSV file is in form of
# Post ID, Comment ID, Question Title, Comment, AnswerStatus, IsReplied, Response, ResponseTime
from Entity_Parser_Record.comment_parser_record import CommentParserRecord
from Entity_Parser_Record.post_parser_record import PostParserRecord
import csv
from nltk.tokenize import sent_tokenize
from Entity_Parser_Record.user_parser_record import UserParserRecord

cpr = CommentParserRecord("Comments.xml")
ppr = PostParserRecord("Posts.xml")
upr = UserParserRecord("Users.xml", "Badges.xml")


def extract_cf():
    # This method reads the comments and generate a list of question titles and first comments on
    # that question with status of question as explained below
    # In previous second method, we just considered the replied status to be receiving an answer from the asker
    # in the next comment, too strict! We aim to consider mentions here. If the asker mentions the CQ poster then
    # that is responded
    result = {}
    counter = 0
    total = 0
    for post_id in cpr.map_of_comments_for_post:
        # list of comments on the post (question id)
        lst_comments = cpr.map_of_comments_for_post[post_id]
        # getting the first comment
        first_comment = lst_comments[0]

        sentences = sent_tokenize(first_comment.text)
        hasquestion = False

        # Checking if there is at least one sentence ending in '?'
        for sent in sentences:
            if sent.strip().endswith("?"):
                hasquestion = True
        if not hasquestion:
            continue

        # Hard constraints for comment to be clarifying question: Be the first, have ? and not have thank
        # We are considering a softer constraint to increase the number of CQ comments and that is
        # Considering the comments before the comment from the asker and check they have ? and no thank

        post_id = first_comment.related_post_id
        if post_id not in ppr.map_questions:
            continue
        question = ppr.map_questions[post_id]
        total += 1

        # Checking if the first comment is not from the asker
        if first_comment.user_id == question.owner_user_id:
            counter += 1
            continue

        # Status has three value of -1,0,1: -1 is where there is no answer given to the question
        # 0 means has at least one answer but it is not accepted answer
        # 1 means it has accepted answer
        status = 0
        if question.accepted_answer_id is not None:
            status = 1
        elif question.answer_count <= 0:
            status = -1

        is_replied = 0
        reply_time = None
        # first jut checking if the next comment is from the question asker then that is a reply
        if len(lst_comments) > 1 and lst_comments[1].user_id is not None and lst_comments[
            1].user_id == question.owner_user_id:
            reply_time = lst_comments[1].creation_date
            is_replied = 1
        else:
            # instead of just checking the next comment, we will check if there is comments with
            # mention of the CQ asker by the question asker in the comments
            user_cq_id = first_comment.user_id
            if user_cq_id is not None and user_cq_id in upr.map_of_user:
                cq_user = upr.map_of_user[user_cq_id]
                if cq_user.display_name is not None and cq_user.display_name != "":
                    user_name = "@" + cq_user.display_name
                    for i in range(2, len(lst_comments)):
                        if lst_comments[i].user_id == question.owner_user_id:
                            if user_name in lst_comments[i].text:
                                is_replied = 1
                                reply_time = lst_comments[i].creation_date
                                break

        result[first_comment.id] = [str(post_id), str(first_comment.id), question.title, first_comment.text,
                                    str(status), str(is_replied), str(reply_time), "CF"]
    return result


def extract_cba():
    # In our previous method we focused on first comments
    # Here is another possible observation; the asker respond back to a comment and that comment is actually a question
    # So we aim to study this in this method and add the information to the previous set of comments that we had
    result = {}
    for post_id in cpr.map_of_comments_for_post:
        lst_comments = cpr.map_of_comments_for_post[post_id]
        for i in range(0, len(lst_comments)):
            comment = lst_comments[i]
            c_user_id = comment.user_id
            post_id = comment.related_post_id
            if post_id not in ppr.map_questions:
                continue
            asker_id = ppr.map_questions[post_id].owner_user_id
            if asker_id != c_user_id:  # The comment is not from the asker
                continue
            # the current comment is from the asker and we are going to check the previous comment properties
            last_comment = lst_comments[i - 1]
            if last_comment.user_id == asker_id:  # The previous comment was also from the question asker
                continue

            sentences = sent_tokenize(last_comment.text)
            hasquestion = False
            for sent in sentences:
                if sent.strip().endswith("?"):
                    hasquestion = True
            if not hasquestion:
                continue
            if last_comment.text.startswith("@"):
                if asker_id not in upr.map_of_user:
                    continue
                else:
                    if not last_comment.text.startswith("@" + upr.map_of_user[asker_id].display_name):
                        continue
            # now we know that the previous comment might have been an actual clarifying question
            question = ppr.map_questions[post_id]
            status = 0
            if question.accepted_answer_id is not None:
                status = 1
            elif question.answer_count <= 0:
                status = -1

            replied = 1
            reply_time = comment.creation_date
            if comment.text.startswith('@'):
                cq_user_id = last_comment.user_id
                if cq_user_id in upr.map_of_user:
                    cq_user = upr.map_of_user[cq_user_id]
                    if cq_user.display_name is not None and cq_user.display_name != "":
                        if not comment.text.startswith("@" + cq_user.display_name):
                            replied = 0
                            reply_time = None
                            for j in range(i + 1, len(lst_comments)):
                                current_com = lst_comments[j]
                                if current_com.user_id == asker_id and "@" + cq_user.display_name in current_com.text:
                                    reply_time = current_com.creation_date
                                    replied = 1

            result[last_comment.id] = [str(post_id), str(last_comment.id), question.title, last_comment.text,
                                       str(status), str(replied), str(reply_time), "CBA"]
    return result


def extract_cma():
    # Lastly we aim to extract those comments that are not in previous format but possible CQ questions
    # They are in question format and posed toward the asker
    result = {}

    for post_id in cpr.map_of_comments_for_post:
        # post_id = comment.related_post_id
        if post_id not in ppr.map_questions:
            continue
        asker_id = ppr.map_questions[post_id].owner_user_id
        lst_comments = cpr.map_of_comments_for_post[post_id]
        for i in range(0, len(lst_comments)):
            comment = lst_comments[i]
            c_user_id = comment.user_id
            # if comment.id in lst_prev_comments_id:  # We are exluding the previous set of comments we have detected, those that were the first comments
            #     continue

            if asker_id == c_user_id:  # The comment is not from the asker
                continue
            sentences = sent_tokenize(comment.text)
            hasquestion = False
            for sent in sentences:
                if sent.strip().endswith("?"):
                    hasquestion = True
            if not hasquestion:
                continue

            if asker_id not in upr.map_of_user or upr.map_of_user[asker_id].display_name is None:
                continue
            mention = "@" + upr.map_of_user[asker_id].display_name
            if mention not in comment.text:
                continue

            # now we know that the comment might have been an actual clarifying question
            question = ppr.map_questions[post_id]
            status = 0
            if question.accepted_answer_id is not None:
                status = 1
            elif question.answer_count <= 0:
                status = -1

            replied = 0
            reply_time = None
            for j in range(i + 1, len(lst_comments)):
                next_comment = lst_comments[j]
                if next_comment.user_id != asker_id:
                    continue
                if not next_comment.text.startswith('@'):
                    reply_time = next_comment.creation_date
                    replied = 1
                else:
                    cq_user_id = comment.user_id
                    if cq_user_id in upr.map_of_user:
                        cq_user = upr.map_of_user[cq_user_id]
                        if cq_user.display_name is not None and cq_user.display_name != "":
                            if next_comment.text.startswith("@" + cq_user.display_name):
                                reply_time = next_comment.creation_date
                                replied = 1
                                break

            result[comment.id] = [str(post_id), str(comment.id), question.title, comment.text, str(status),
                                  str(replied), str(reply_time), "CMA"]
    return result


def generate_file(result_file_path):
    results_a = extract_cf()
    results_b = extract_cba()
    results_c = extract_cma()
    file = open(result_file_path, "w", newline='')
    writer = csv.writer(file, delimiter='\t', lineterminator='\n')
    for key in results_a:
        writer.writerow(results_a[key])
    for key in results_b:
        writer.writerow(results_b[key])
    temp = list(results_a.keys())
    temp.extend(list(results_b.keys()))
    key_c = set(results_c) - set(temp)
    for key in key_c:
        writer.writerow(results_c[key])
    file.close()


generate_file("MathCQs.tsv")
