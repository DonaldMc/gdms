# - Coding UTF8 -
#
# Networked Decision Making
# Development Sites (source code): http://github.com/DonaldMcC/gdms
#
# Demo Sites (Pythonanywhere)
#   http://netdecisionmaking.com/nds/
#   http://netdecisionmaking.com/gdmsdemo/
#
# License Code: MIT
# License Content: Creative Commons Attribution 3.0
#
# Also visit: www.web2py.com
# or Groups: http://groups.google.com/group/web2py
# For details on the web framework used for this development
#
# With thanks to Guido, Massimo and many other that make this sort of thing
# much easier than it used to be


import datetime

if __name__ != '__main__':
    from gluon import *
    from ndspermt import get_exclude_groups, get_groups
    from graph_funcs import conv_for_iter, iter_dfs, get_trav_list
    
    
def convxml(value, tag):
    return '<' + tag + '>' + str(value) + '</' + tag + '>'


def convrow(row, dependlist=''):
    # pDepend is a list of taskst that this item depends upon
    # pLink will be the url to edit the action which can be derived from the row id
    # expect dependlist will need to be stripped
    colorclass = gantt_colour(row.startdate, row.enddate, row.perccomplete)
    plink = URL('submit','question_plan',args=['quest',row.id], extension='html')
    projrow = '<task>'
    projrow += convxml(row.id, 'pID')
    projrow += convxml(row.questiontext, 'pName')
    projrow += convxml(row.startdate, 'pStart')
    projrow += convxml(row.enddate, 'pEnd')
    projrow += convxml(colorclass, 'pClass')
    projrow += convxml(plink, 'pLink')
    projrow += convxml('', 'pMile')
    projrow += convxml(row.responsible, 'pRes')
    projrow += convxml(row.perccomplete, 'pComp')
    projrow += convxml('', 'pGroup')
    projrow += convxml('', 'pParent')
    projrow += convxml(dependlist, 'pDepend')
    projrow += convxml('A caption', 'pCaption')
    projrow += convxml(row.notes, 'pNotes')            
    projrow += '</task>'
    return projrow


def gantt_colour(startdate, enddate, percomplete=0, gantt=True):

    """
    .gtaskyellow, Complete
    .gtaskblue, Not started and before startdate
    .gtaskred, Overdue and not complete
    .gtaskgreen, Started and on track
    .gtaskpurple, Started and behind schedule
    .gtaskpink Later  
    
    ganntt is now a flag to allow coding of plan rows with same logic """

    if startdate and enddate:
        now = datetime.datetime.now()
        dayselapsed = max(now-startdate,datetime.timedelta(days=0)).days
        daysduration = max(enddate-startdate, datetime.timedelta(days=0)).days
        percelapsed = min((100 * dayselapsed) / daysduration, 100)

        if percomplete == 100:
            colorclass = 'gtaskyellow'
        elif now < startdate:
            colorclass = 'gtaskblue'
        elif now > enddate:
            colorclass = 'gtaskred'
        elif percelapsed > percomplete:
            colorclass = 'gtaskpurple'
        else:
            colorclass = 'gtaskgreen'
    else:
        colorclass = 'gtaskpink'  # not sure ever worth returning as no bar without dates
    
    if gantt is False:
        colorclass = colorclass[1:]
        
    return colorclass
    
    
def resulthtml(questiontext, answertext, id=0, output='html'):
    
    """This formats the email for sending from the schedule on email resolution 
    """
    
    params = current.db(current.db.website_parameters.id > 0).select().first()
    stripheader = params.website_url[7:] # to avoid duplicated header
    if output == 'html':
        result = '<p>' + questiontext + r'</p>'
        result += r'<p>Users have resolved the correct answer is:</p>'
        result += '<p>' + answertext + r'</p>'
        result += URL('viewquest', 'index', args=[id], scheme='http', host=stripheader)
        result = '<html>'+result + r'</html>'
    else:
        result = questiontext + '/n Users have resolved the correct answer is: /n' + answertext
    return result

    
def email_setup(periods = ['Day', 'Week', 'Month'], refresh=False):
    # This will setup a daily, weekly and monthly record in the file
    # Daily will be for current day, weekly for current week and monthly for current month
    # It will then schedule a task which runs daily and that will then run the actual activity
    # task
    for x in periods:
        startdate, enddate = getrundates(x)
        existrows = current.db((current.db.email_runs.runperiod == x) & (current.db.email_runs.status == 'Planned')
                               ).select()
        if existrows:
            existrow = existrows.first()
            if refresh is True:  # Running a rollforward
                startdate = existrow.dateto
            existrow.update(datefrom=startdate,dateto=enddate)
        else:
            current.db.email_runs.insert(runperiod=x, datefrom=startdate, dateto=enddate, status='Planned')
    return True

    
def updatequestcounts(qtype, oldcategory, newcategory, oldstatus, newstatus, answergroup):
    """This will now take the old and new category and the old and new status.  The answergroup should never change so
       only there if status has changed to update the answergroup counts
    `  1 nothing changes - may call to debug
       2 status change - update questcounts on existing record and update answergroup counts
       3 category change - reduce questcount at old status and increase questcount on different record for new
         status
       4 category and status change """

    if oldcategory == newcategory and oldstatus == newstatus:
        return

    # get existing category record should always exist
    existrow = current.db((current.db.questcount.groupcatname == oldcategory) & (current.db.questcount.groupcat == 'C')).select().first()

    oldindex = getindex(qtype, oldstatus)
    newindex = getindex(qtype, newstatus)
    qcount = existrow.questcounts
    qcount[oldindex] -= 1
    
    if oldcategory == newcategory:
        qcount[newindex] += 1
    existrow.update_record(questcounts=qcount)

    if oldcategory != newcategory:
        newrows = current.db((current.db.questcount.groupcatname == newcategory) & (current.db.questcount.groupcat == 'C')).select()
        if newrows:
            newrow = newrows.first()
            qcount = newrow.questcounts
            qcount[newindex] += 1
            newrow.update_record(questcounts=qcount)
        else:
            createcount = [0] * 18
            createcount[newindex] = 1
            current.db.questcount.insert(groupcat='C', groupcatname=newcategory, questcounts=createcount)
    # udpate the group count record if status changed
    if oldstatus != newstatus:
        grouprow = current.db((current.db.questcount.groupcatname == answergroup) & (current.db.questcount.groupcat == 'G')).select().first()
        if grouprow:
            qcount = grouprow.questcounts
            qcount[oldindex] -= 1
            qcount[newindex] += 1
            grouprow.update_record(questcounts=qcount)
        else:
            print('An error occurred updating group quest counts')
    return


def update_question(questid, userid):
    """
    This procedure updates the question and userquestion records after each answer
    The update is in 2 parts.  The number of answers and so on are
    always updated however the main scoring only happens when we have 3 or more
    unprocessed answers. so there is a case to separate into two functions however reluctant 
    to push scoring onto scheduler as user need to know immediately if they solved the question
    however score lower level should probably be scheduled
    only call score_question if sufficient unprocessed answers  

    When this is a module it is not posting userquestion updates as we don't know the user and the first
    part of what is in the controller is not called - plan will be to get this working for quick questions
    and then call all the time once this works it may get merged into score question but with separate
    function to address resolved question??

    :param questid:
    :param userid:
    """

    quest = db(current.db.question.id == questid).select().first()

    answers_per_level = 3

    # first step is to select the related user and question records their should
    # only ever be one of each of these and we update as much as possible here 
    # because it's interesting to see as much as possible on viewquest rather
    # than waiting until 3 people have answered and it can be scored - however this can result in
    # a degree of double updating

    if quest.intunpanswers >= answers_per_level:
        redirect(URL('score_question', args=quest.id))
    else:
        # need to have another look at this 
        # intunpanswers < answers_per_level
        # the general requirement here is to do nothing - however because the
        # solution focuses on solving the highest priority question at all times
        # different users may be sent the same question at the same time and
        # answers may be received for a level after the question is either promoted
        # or resolved - promotions shouldn't be an issue but resolved questions are
        # because the user should probably get credit if right and nothing if wrong
        # and an explanation of what happend

        if quest.status == 'Resolved' or quest.status == 'Agreed':
            # get the score - if right add to score - if wrong same
            # update userquestion and user - other stuff doesn't apply
            # scoretable = current.db(current.db.scoring.level == quest.level).select(cache=(cache.ram, 1200), cacheable=True).first()
            scoretable = current.db(current.db.scoring.level == quest.level).select().first()
            if scoretable is None:
                score = 30
                wrong = 1
            else:
                if quest.qtype != 'action':
                    score = scoretable.correct
                    wrong = scoretable.wrong
                else:
                    score = scoretable.rightaction
                    wrong = scoretable.wrongaction
            numcorrect = 0
            numwrong = 0
            numpassed = 0

            if uq.answer == quest.correctans:
                updscore = score
                numcorrect = 1
            elif uq.answer == 0:
                updscore = 1
                numpasse = 1
            else:
                updscore = wrong
                numwrong = 1

            uq.update_record(status='Resolved', score=updscore, resolvedate=request.utcnow)

            updateuser(userid, updscore, numcorrect, numwrong, numpassed)

        redirect(URL('viewquest', 'index', args=quest.id))


def score_question(questid, uqid=0, endvote=False):
    """
    This routine is now called for all answers to questions and it will also be
    called for vote style questions
    """

    answers_per_level = 3  # To be replaced with record
    answers_to_resolve = 3
    method = 'Network'

    status = 'In Progress'

    quest = current.db(current.db.question.id == questid).select().first()
    resmethods = current.db(current.db.resolve.resolve_name == quest.resolvemethod).select()

    if resmethods:
        resmethod = resmethods.first()
        answers_per_level = resmethod.responses
        method = resmethod.resolve_method
    
    if uqid:
        uq = current.db.userquestion[uqid]

        # first step is to select the related user and question records their should
        # only ever be one of each of these and we update as much as possible here
        # because it's interesting to see as much as possible on viewquest rather
        # than waiting until 3 people have answered and it can be scored - however this can result in
        # a degree of double updating

        # do weighted averaging of urgency and importance based on userquest and this is
        # accepted from passers
        if uq:
            urgency = (((quest.urgency * quest.totanswers()) + uq.urgency) /
                       (quest.totanswers() + 1))
            importance = (((quest.importance * quest.totanswers()) + uq.importance) /
                          (quest.totanswers() + 1))

            anscount = quest.answercounts
            anscount[uq.answer] += 1
            intunpanswers = quest.unpanswers + 1

            current.db(current.db.question.id == quest.id).update(answercounts=anscount,
                                                                  urgency=urgency, importance=importance,
                                                                  unpanswers=intunpanswers)

            update_numanswers(uq.auth_userid)
    else:
        intunpanswers = quest.unpanswers
        urgency = quest.urgency
        importance = quest.importance

    if (intunpanswers >= answers_per_level and method == 'Network') or endvote:

        # if intunpanswers >= answers_per_level:
        # this was always true in old structure probably not now as may handle votes this way
        # scorequestions - need to get all the answers first at this level -
        # should agree to unpanswers and should be a small number - so lets fully
        # score these - if they don't agree to unpanswers then doesn't agree
        # and will need to be escalated - so simple score if resolved - lower
        # levels will probably be done as a background task eventually so seems
        # ok this should never happen on a passed question at present challengees
        # are not getting credit for right or wrong challenges - this will be
        # added in a subsequent update not that complicated to do however

        level = quest.question_level

        scoretable = current.db(current.db.scoring.scoring_level == level).select(
                                cache=(current.cache.ram, 1200), cacheable=True).first()
        if scoretable is None:
            score = 30
            wrong = 1
            submitter = 1
        else:
            submitter = scoretable.submitter
            if quest.qtype == 'quest':
                score = scoretable.correct
                wrong = scoretable.wrong
            else:
                score = scoretable.rightaction
                wrong = scoretable.wrongaction

        # so basic approach to this is a two pass approach first pass
        # should total the answers establish if majority want to reject, change category
        # or change geography and if it meets resolution criteria which will now come from a questtype
        unpanswers = current.db((current.db.userquestion.questionid == questid) &
                        (current.db.userquestion.status == 'In Progress') &
                        (current.db.userquestion.uq_level == level)).select()

        numanswers = [0] * len(quest.answercounts)
        # numanswers needs to become a list or dictionary
        numreject = 0
        numchangecat = 0
        updatedict = {'unpanswers': 0}
        ansreason=''
        ansreason2=''
        ansreason3=''
        # scopedict = {}
        catlist = []
        scopelist = []
        contlist = []
        countrylist = []
        locallist = []
        answerlist = [] 

        for row in unpanswers:
            numanswers[row.answer] += 1
            numreject += row.reject
            catlist.append(row.category)
            scopelist.append(row.activescope)
            contlist.append(row.continent)
            countrylist.append(row.country)
            locallist.append(row.subdivision)       

        if (max(numanswers) >= ((len(unpanswers) * resmethod.consensus) / 100) or
            method == 'Vote'):  # all answers agree or enough for consensues or vote is being resolved
            status = 'Resolved'
            correctans = numanswers.index(max(numanswers))
            updatedict['correctans'] = correctans
        elif (numreject * 2) > answers_per_level:  # majority reject
            status = 'Rejected'
            correctans = -1
        else:
            # insufficient consensus so promote to next level
            level += 1
            updatedict['question_level'] = level
            status = 'In Progress'
            correctans = -1

        # update userquestion records
        # this is second pass through to update the records
        for row in unpanswers:
            # for this we should have the correct answer
            # update userquestion records to being scored change status
            # however some users may have passed on this question so need
            # a further condition and the question is still resolved
            # also need to consider the change scope and change category
            # but only if a majority want this otherwise will stay as is
            # change cat and change scope are slightly different as change
            # of scope might be agreed but the correct continent or country
            # may differ in which case the question will have scope changed
            # but continent or country unchanged

            numcorrect = 0
            numwrong = 0
            numpassed = 0

            if row.answer == correctans and correctans > -1:  # user got it right
                numcorrect = 1
                # update the overall score for the user
                updscore = score
                if row.answerreason != '':
                    if ansreason == '':
                        ansreason = row.answerreason
                        updatedict['answerreasons'] = ansreason
                    elif ansreason2 == '':
                        ansreason2 = row.answerreason
                        updatedict['answerreason2'] = ansreason2
                    else:
                        ansreason3 = row.answerreason
                        updatedict['answerreason3'] = ansreason3
                elif row.answer == -1:  # user passed
                    numpassed = 1
                    updscore = 1
                elif correctans == -1:  # not resolved yet
                    numwrong = 0
                    updscore = 0
                else:  # user got it wrong - this is now possible as unanimity not reqd
                    numwrong = 1
                    updscore = wrong

                if status == 'Resolved':
                    row.update_record(status=status, score=updscore, resolvedate=current.request.utcnow,
                    startdate=current.request.utcnow, enddate=current.request.utcnow)
                else:
                    row.update_record(status=status, score=updscore)

                updateuser(row.auth_userid, updscore, numcorrect, numwrong, numpassed)

        # update the question to resolved or promote as unresolved
        # and insert the correct answer values for this should be set above
        #scopetext = quest.scopetext
        oldcategory = quest.category
        oldstatus = quest.status
        
        numrequired = answers_per_level / 2.0
        updatedict['category'] = check_change(catlist, numrequired, quest.category)
        suggestscope = check_change(scopelist, numrequired, quest.activescope)
        suggestcont = check_change(contlist, numrequired, quest.continent)
        suggestcountry = check_change(countrylist, numrequired, quest.country)
        suggestlocal = check_change(locallist, numrequired, quest.subdivision)
        
        updatedict['activescope'] = suggestscope
        updatedict['continent'] = suggestcont
        updatedict['country'] = suggestcountry
        updatedict['subdivision'] = suggestlocal

        updstatus = status
        if quest.qtype != 'quest':
            if correctans == 0:
                updstatus = 'Agreed'
            else:
                updstatus = 'Disagreed'
        if updstatus != quest.status:
            updatedict['status'] = updstatus
            updatedict['resolvedate'] = current.request.utcnow
            changestatus = True

        # lines added to avoid error on recalc of computed field
        updatedict['urgency'] = quest.urgency
        updatedict['importance'] = quest.importance

        current.db(current.db.question.id == quest.id).update(**updatedict)

        updatequestcounts(quest.qtype, oldcategory, updatedict['category'], oldstatus, updstatus, quest['answer_group'])

        if status == 'Resolved' and level > 1:
            score_lowerlevel(quest.id, correctans, score, level, wrong)
            # TODO this needs retested
            if quest.challenge is True:
                if correctans == quest.correctans:
                    successful = False
                else:
                    successful = True
                score_challenge(quest.id, successful, level)
                print('running score challenge')

    return status

    
def most_common (lst):
    """ initial discussion on ways of doing this at:
    http://stackoverflow.com/questions/1518522/python-most-common-element-in-a-list
    >>> most_common(['a','b','c','b'])
    ('b', 2)
    
    """
    return max(((item, lst.count(item)) for item in set(lst)), key=lambda a: a[1])


def check_change(lst, numrequired, unchangedvalue):
    """ 
    >>> check_change(['a','b','c','b'],2,'a')
    'b'
    
    >>> check_change(['a','b','c','b'],3,'a')
    'a'
    
    """
    result, qty = most_common(lst)
    if qty < numrequired:
        result = unchangedvalue
    return(result)
    

def getindex(qtype, status):
    """This returns the index for questcounts which is a list of integers based on the 6 possible status and 3 question
       types so it is an index based on two factors want 0, 1 or 2 for issue, question and action and then 0 through 5
       for draft, in progress, etc - need to confirm best function to do this with
    :param qtype: string
    :param status: string

    >>> getindex('quest','In Progress')
    7
    """

    qlist = ['issue', 'quest', 'action']
    slist = ['Draft', 'In Progress', 'Resolved', 'Agreed', 'Disagreed', 'Rejected']

    i = qlist.index(qtype) if qtype in qlist else None
    j = slist.index(status) if status in slist else None

    return (i * 6) + j


def userdisplay(userid):
    """This should take a user id and return the corresponding
       value to display depending on the users privacy setting"""
    usertext = userid
    userpref = current.db(current.db.auth_user.id == userid).select().first()
    if userpref.privacypref=='Standard':
        usertext = userpref.first_name + ' ' + userpref.last_name
    else:
        usertext = userid
    return usertext


def scopetext(scopeid, continent, country, subdivision):
    """This returns the name of the relevant question scope """
    
    scope = current.db(current.db.scope.id == scopeid).select(current.db.scope.description).first().description
    if scope == 'Global':
        activetext = 'Global'
    elif scope == 'Continental':
        activetext = current.db(current.db.continent.id == continent).select(
            current.db.continent.continent_name).first().continent_name
    elif scope == 'National':
        activetext = current.db(current.db.country.id == country).select(
            current.db.country.country_name).first().country_name
    else:
        activetext = current.db(current.db.subdivision.id == subdivision).select(
            current.db.subdivision.subdiv_name).first().subdiv_name

    return activetext


def truncquest(questiontext, maxlen=600, wrap=0, mark=True):
    if mark:
        if len(questiontext) < maxlen:
            txt = MARKMIN(questiontext)
        else:
            txt = MARKMIN(questiontext[0:maxlen] + '...')
    else:
        if len(questiontext) < maxlen:
            txt = questiontext
        else:
            txt = questiontext[0:maxlen] + '...'
    return txt


def disp_author(userid):
    if userid is None:
        return ''
    else:
        user = current.db.auth_user(userid)
        return '%(first_name)s %(last_name)s' % userid


def updateuser(userid, score, numcorrect, numwrong, numpassed):
    user = current.db(current.db.auth_user.id == userid).select().first()
    # Get the score required for the user to get to next level
    scoretable = current.db(current.db.scoring.scoring_level == user.userlevel).select(
        cache=(current.cache.ram, 1200), cacheable=True).first()

    if scoretable is None:
        nextlevel = 1000
    else:
        nextlevel = scoretable.nextlevel

    updscore = user.score + score

    if updscore > nextlevel:
        userlevel = user.userlevel + 1
    else:
        userlevel = user.userlevel

    user.update_record(score=updscore, numcorrect=user.numcorrect + numcorrect,
                       numwrong=user.numwrong + numwrong, numpassed=user.numpassed + numpassed,
                       user_level=userlevel)
    # stuff below removed for now as not working and want this to run as background scheduler task so makes no sense
    # to have here in this context
    # if auth.user.id == userid:  # update auth values
    #    auth.user.update(score=updscore, level=userlevel, rating=userlevel, numcorrect=
    #                             auth.user.numcorrect + numcorrect, numwrong=auth.user.numwrong + numwrong,
    #                             numpassed=auth.user.numpassed + numpassed)

    return True


def update_numanswers(userid):
    # This just increments numb users
    isauth = current.session.auth or None
    if isauth and userid == current.auth.user.id: # This should always be the case
        numquests = current.auth.user.numquestions + 1
        current.db(current.db.auth_user.id == current.auth.user.id).update(numquestions=numquests)
        current.auth.user.update(numquestions=numquests)
    return True


def score_lowerlevel(questid, correctans, score, level, wrong):
    """
    This may eventually be a cron job but for debugging it will need to be
    called from score_question basic approach is just to go through and update
    all the lower levels and if correct they get the values
    of the question which will probably be higher the higher the level it got
    resolved at so this isn't too complicated - but need to be passed the
    question-id, the correct answer and the number of
    points for correct and number for wrong - lets do later once main process
    working.
    Users get points for the level the question resolved at but need to acquire
    the level of points to move up from their level

    This needs some further work to cater for challenge questions which have a
    different 2nd resolved answer
    thinking is the original correct answers can stay because it was reasonable
    but those that got it wrong
    at lower levels should get some credit - however not critical for now -
    lets publish and see what other people consider best approach to this -
    it is not clear cut - nor critical to the principal of
    what we are trying to to do

    scoretable = current.db(current.db.scoring.level==level).select().first()
    score = scoretable.correct
    there should be no need to assess changes to categories or scope
    in this process as these will all have been considered in previous rounds
    and the auth user running this should always be a user at the top level
    so no issues with auth not updating either - so we should be good to go
    :param questid:
    """

    status = 'Resolved'

    unpanswers = current.db((current.db.userquestion.questionid == questid) &
                    (current.db.userquestion.status == 'In Progress')).select()

    for row in unpanswers:
        # work out if the question was correct or not
        if row.answer == correctans:
            actscore = score
            numcorrect = 1
            numwrong = 0
        elif row.answer == 0:
            actscore = 1
            numcorrect = 0
            numwrong = 0
        else:
            actscore = wrong
            numcorrect = 0
            numwrong = 1

        # update userquestion records to being scored change status
        current.db(current.db.userquestion.id == row.id).update(score=actscore, status=status, resolvedate=current.request.utcnow)
        # update the overall score for the user
        user = current.db(current.db.auth_user.id == row.auth_userid).select().first()
        updscore = user.score + actscore
        level = user.userlevel
        scoretable = current.db(current.db.scoring.scoring_level == level).select(cache=(current.cache.ram, 1200), cacheable=True).first()
        nextlevel = scoretable.nextlevel

        if updscore > nextlevel:
            userlevel = user.userlevel + 1
        else:
            userlevel = user.userlevel

        current.db(current.db.auth_user.id == row.auth_userid).update(score=updscore,
                                                      userlevel=userlevel, rating=user.userlevel + userlevel,
                                                      numcorrect=user.numcorrect + numcorrect,
                                                      numwrong=user.numwrong + numwrong)
    return


def score_challenge(questid, successful, level):
    """
    This will reward those that raised a challenge if the answer has changed
    it may also spawn an issue of scoring users who previously thought they
    got it wrong but now got it right - thinking is we wouldn't remove
    points from those that were previously considered right
    :param successful:
    :param questid:
    :param level:
    """

    unpchallenges = current.db((current.db.questchallenge.questionid == questid) &
                       (current.db.questchallenge.status == 'In Progress')).select()

    # should get the score based on the level of the question
    # and then figure out whether
    # get the score update for a question at this level
    scoretable = current.db(current.db.scoring.scoring_level == level).select().first()

    if scoretable is None:
        rightchallenge = 30
        wrongchallenge = -10
    else:
        rightchallenge = scoretable.rightchallenge
        wrongchallenge = scoretable.wrongchallenge

    for row in unpchallenges:
        # update the overall score for the user
        user = current.db(current.db.auth_user.id == row.auth_userid).select().first()
        if successful is True:
            updscore = user.score + rightchallenge
        else:
            updscore = user.score + wrongchallenge

        scoretable = current.db(current.db.scoring.scoring_level == user.userlevel).select().first()
        nextlevel = scoretable.nextlevel

        if updscore > nextlevel:
            userlevel = user.userlevel + 1
        else:
            userlevel = user.userlevel

        current.db(current.db.auth_user.id == row.auth_userid).update(score=updscore, userlevel=userlevel)

    return


def getitem(qtype):
    if qtype == 'quest':
        item = 'question'
    elif qtype == 'action':
        item = 'action'
    else:
        item = 'issue'
    return item


def getrundates(period='Day', startdate=datetime.datetime.today()):
    """
    :param startdate:
    :param period: Valid values are Day, Week or Month
    :return startdate, endate
    So this is a bit crude at moment but not sure I want calendar weeks and months either
    Leave for now
    """

    numdays = (period == 'Day' and 1) or (period == 'Week' and 7) or 30
    enddate = startdate + datetime.timedelta(days=numdays)
    return startdate, enddate


def creategraph(itemids, numlevels=0, intralinksonly=True):
    """
    :param itemids: list
    :param numlevels: int
    :param intralinksonly: boolean
    :return: graph details

    Now think this will ignore eventmap and do no layout related stuff which means events are irrelevant for this
    function it should get links for itemids in an iterable manner and so build of network.py  mainly
    when called from event it will have a list of item ids only from the event already established

    """

    query = current.db.question.id.belongs(itemids)
    quests = current.db(query).select()

    if intralinksonly:
        # in this case no need to get other questions
        intquery = (current.db.questlink.targetid.belongs(itemids)) & (current.db.questlink.status == 'Active') & (
                    current.db.questlink.sourceid.belongs(itemids))

        # intlinks = current.db(intquery).select(cache=(cache.ram, 120), cacheable=True)
        links = current.db(intquery).select()
    else:
        parentlist = itemids
        childlist = itemids

        parentquery = (current.db.questlink.targetid.belongs(parentlist)) & (current.db.questlink.status == 'Active')
        childquery = (current.db.questlink.sourceid.belongs(itemids)) & (current.db.questlink.status == 'Active')

        links = None
        # just always have actlevels at 1 or more and see how that works
        # below just looks at parents and children - to get partners and siblings we could repeat the process
        # but that would extend to ancestors - so probably need to add as parameter to the query but conceptually
        # this could be repeated n number of times in due course

        # these may become parameters not sure
        # change back to true once working
        getsibs = False
        getpartners = False

        for x in range(numlevels):
            # ancestor proces
            if parentlist:
                # if not request.env.web2py_runtime_gae:
                parentlinks = current.db(parentquery).select()
                # else:
                #    parentlinks = None
                if links and parentlinks:
                    links = links | parentlinks
                elif parentlinks:
                    links = parentlinks
                if parentlinks:
                    mylist = [y.sourceid for y in parentlinks]
                    query = current.db.question.id.belongs(mylist)
                    parentquests = current.db(query).select()

                    quests = quests | parentquests
                    parentlist = [y.id for y in parentquests]
                    if getsibs:
                        sibquery = current.db.questlink.sourceid.belongs(parentlist) & (current.db.questlink.status == 'Active')
                        siblinks = current.db(sibquery).select()
                        if siblinks:
                            links = links | siblinks
                            mylist = [y.targetid for y in siblinks]
                            query = current.db.question.id.belongs(mylist)
                            sibquests = current.db(query).select()
                            quests = quests | sibquests

                        # parentquery = current.db.questlink.targetid.belongs(parentlist)

                        # child process starts
            if childlist:
                # if not request.env.web2py_runtime_gae:
                childlinks = current.db(childquery).select()
                # else:
                #    childlinks = None
                if links and childlinks:
                    links = links | childlinks
                elif childlinks:
                    links = childlinks
                # childcount = current.db(childquery).count()
                # resultstring=str(childcount)
                if childlinks:
                    mylist = [y.targetid for y in childlinks]
                    query = current.db.question.id.belongs(mylist)
                    childquests = current.db(query).select()
                    quests = quests | childquests
                    childlist = [y.id for y in childquests]
                    if getpartners:
                        partquery = current.db.questlink.targetid.belongs(childlist)
                        partlinks = current.db(partquery).select()
                        if partlinks:
                            links = links | partlinks
                            mylist = [y.sourceid for y in partlinks]
                            query = current.db.question.id.belongs(mylist) & (current.db.questlink.status == 'Active')
                            partquests = current.db(query).select()
                            quests = quests | partquests
                            # childquery = current.db.questlink.sourceid.belongs(childlist)

    questlist = [y.id for y in quests]
    if links:
        linklist = [(y.sourceid, y.targetid) for y in links]
        links = links.as_list()
    else:
        linklist = []
    return dict(questlist=questlist, linklist=linklist, quests=quests, links=links, resultstring='OK')


def geteventgraph(eventid, redraw=False, grwidth=720, grheight=520, radius=80, status='Open'):
    # this should only need to use eventmap
    # now change to use quest
    stdwidth = 1000
    stdheight = 1000
    resultstring = 'OK'
    linklist = []
    links = None
    intlinks = None
    nodepositions={}

    quests, questlist = getevent(eventid, status)
    # print(questlist)
    if not questlist:
        resultstring = 'No Items setup for event'
    else:
        intlinks = getlinks(questlist)
        links = [x.sourceid for x in intlinks]
        
        if links:
            linklist = [(x.sourceid, x.targetid, {'weight': 30}) for x in intlinks]

        if redraw and status != 'Archived':
            nodepositions = getpositions(questlist, linklist)
            for row in quests:
                row.update_record(xpos=(nodepositions[row.id][0] * stdwidth), ypos=(nodepositions[row.id][1] * stdheight))
                nodepositions[row.id][0] = ((nodepositions[row.id][0] * grwidth) / stdwidth) + radius
                nodepositions[row.id][1] = ((nodepositions[row.id][0] * grheight) / stdheight) + radius
        else:
            nodepositions = {}
            for row in quests:
                nodepositions[row.id] = (((row.xpos * grwidth) / stdwidth) + radius, ((row.ypos * grheight) / stdheight) + radius)

    return dict(questlist=questlist, linklist=linklist, quests=quests, links=intlinks, nodepositions=nodepositions,
                resultstring=resultstring)

    
def getevent(eventid, status="Open", orderby='id'):
    if orderby == 'Event':
        orderstr = current.db.question.xpos
    else:
        orderstr = current.db.question.id
    if status == 'Archived':
        quests = current.db(current.db.eventmap.eventid == eventid).select()
        questlist = [x.questid for x in quests]
    else:
        quests = current.db(current.db.question.eventid == eventid).select(orderby=orderstr)
        questlist = [x.id for x in quests]
    return quests, questlist

    
def getlinks(questlist):
    intquery = (current.db.questlink.targetid.belongs(questlist)) & (current.db.questlink.status == 'Active') & (
                    current.db.questlink.sourceid.belongs(questlist))
    intlinks = current.db(intquery).select()
    return intlinks


    

def generate_thumbnail(image, nx=120, ny=120, static=False):
    """
    Makes thumbnail version of given image with given maximum width & height
    in uploads folder with filename based on original image name

    If static=True thumbnail will be placed in static/thumbnails
    so it can be used without the need of a download controller

    requires PIL
    """
    if not image:
        return
    try:
        import os
        from PIL import Image

        img = Image.open(os.path.join(request.folder, 'uploads', image))
        img.thumbnail((nx, ny), Image.ANTIALIAS)
        root, ext = os.path.splitext(image)
        thumb = '%s_thumb_%s_%s%s' % (root, nx, ny, ext)
        img.save(os.path.join(request.folder, 'uploads', thumb))
        if static:
            file_dir = os.path.join(request.folder, 'static', 'thumbnails')
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            img.save(os.path.join(file_dir, thumb))
            os.path.join(file_dir, thumb)
        return thumb
    except:
        return

def _test():
    import doctest
    doctest.testmod()
        
if __name__ == '__main__':
    # Can run with -v option if you want to confirm tests were run
    _test()
