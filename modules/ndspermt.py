# - Coding UTF8 -
#
# Networked Decision Making
# Site: http://code.google.com/p/global-decision-making-system/
#
# License Code: GPL, General Public License v. 2.0
# License Content: Creative Commons Attribution 3.0
#
# Also visit: www.web2py.com
# or Groups: http://groups.google.com/group/web2py
# 	For details on the web framework used for this development
#
# Developed by Russ King (newglobalstrategy@gmail.com
# Russ also blogs occasionally to pass the time at proudofyourplanent.blogspot.com
# His general thinking on why this project is very important is availalbe at
# http://www.scribd.com/doc/98216626/New-Global-Strategy


from gluon import *

def get_groups(userid=None):
    """This should return a list of groups that a user has access to it now requires a login to
     be passed and currently only used on submit and questcountrows with user so no need to handle none"""

    db = current.db
    accessgrouprows = db(db.group_members.auth_userid == userid).select()
    access_group = [x.access_group.group_name for x in accessgrouprows]
    access_group.append('Unspecified')

    return access_group

def get_exclude_groups(userid=None):
    """This should return a list of groups that a user does not have access to it now requires a login to
     be passed and currently only used on submit and questcountrows with user so no need to handle none"""

    db = current.db
    accessgroups = db(db.access_group.id>0).select()
    allgroups = [x.group_name for x in accessgroups]
    exclude_group = list(set(allgroups) - set(get_groups(userid)))

    return exclude_group

''' now have a few functions to think about here
    1) Can a user view a question?
        Change here is to have  a function check if question has a group then user must belong to that group
        think this is submitted with the group of the question - but potentially this can just be a call to get groups
        only required in viewquest for now
        So - this is can_view

    2) Can a user join a group?
        Yes if public, otherwise could apply if apply and won't see groups that are invite only or admin unless they are
        already members of them - need to figure out options for each group
        
        implemented as join_group

    3) Can a user edit a group?
        Yes if the owner or an admin of the group and one admin can appoint others

        to implement as group_actions

    4) Can a user delete a group?
        Only possible by the owner and if no questions are assigned - otherwise deactivate
        to implement as group_actions        

    5) Can a user add a question/action or issue to an event?
        Yes if event is shared or they are the owner of the event - however question needs to be unassigned to another
        event
    6) Can a user submit a question to a group?
        Yes if member of the group - otherwise no - so no function required at present

    7) Can a user answer a question, action or issue?
        Yes unless group policy blocks selecting questions to answer - and currently putting through the can_view routine first
        but this may need an answerable function

    8) Can a user vote on a question
        Yes if part of group that question assigned to and haven't voted before - not clear if we should allow change of
        mind - but no obvious reason not to

Above will do for now - in general we cant use decorated functions for these as need to evaluate which event, question
etc the user is attempting to answer/view

    Whole approach to votes in progress is probably missing bit of the framework now - but think votes are completely separate as they 
    have expiry dates and so forth - and they can change from one to the other - possibly until resolved - would just be a question of updating
    the count - but lets keep separate for now - so it can be a dimension - lets start to get that in place 


'''

def can_view(qtype, status, resolvemethod, hasanswered, answer_group):
    viewable = False
    message = ''
        
    return (viewable, message)


def join_groups(userid):
    """This should return a list of groups that a user has access to it now requires a login to
     be passed and currently only used on submit and questcountrows with user so no need to handle none"""

    db = current.db
    accessgrouprows = db(db.group_members.auth_userid == userid).select()
    access_group = [x.access_group.group_name for x in accessgrouprows]
    access_group.append('Unspecified')

    return access_group


def get_actions(qtype, status, resolvemethod,  owner, userid, hasanswered, context='std'):
    avail_actions=[]
    if status == 'In Progress' and (qtype == 'issue' or qtype == 'action') and hasanswered is False:
        avail_actions = ['Approve','Disapprove']
    elif status == 'Resolved' or status == 'Agreed':
        avail_actions = ['Agree', 'Disagree']
    elif status == 'Draft' and owner == userid:
        avail_actions = ['Edit']
    if context == 'View':
        if qtype == 'action':
            avail_actions.append('Next_Action')
            avail_actions.append('Link_Action')
        elif qtype == 'issue':
            avail_actions.append('Next_Issue')
            avail_actions.append('Link_Question')
            avail_actions.append('Link_Action')
        else:
            avail_actions.append('Next_Question')
            avail_actions.append('Link_Question')
            avail_actions.append('Link_Action')
    else:
        avail_actions.append('View')
    #may change this to return both buttons but one would be hidden somehow
    if context == 'event':
        avail_actions.append('Link')
    elif context == 'evtunlink':
        avail_actions.append('Unlink')
    return avail_actions


def make_button(action, id, context='std', rectype='quest'):
    """This should return a button with appropriate classes for an action in a given context this will typiclly 
       be called by a get_buttons function which will take call get actions to get the actions and then make
       a button for each action There are currently 9 possible actions in the get_actions list:
       Approve, Disapprove, Pass and Reject for quick resolution and
       Agree, Disagree, Challenge and Details which are all currently setup on viewquest but not as TAG.INPUT

       So I think that is phase 1 and then put in as buttons -the structure of review is also worth looking at"""

    #Below is result for call to link question to event
    #<INPUT TYPE=BUTTON class="btn btn-primary btn-xs" onclick="ajax('{{=URL('event','link',args=[eventrow.id,row.id,'link'])}}',
    #  ['challreason'], 'target')" VALUE="Link"></td>
    session=current.session
    stdclass = "btn btn-primary  btn-xs btn-group-xs"
    if rectype == 'quest':
        if action == 'Agree':
            stringlink = XML("ajax('" + URL('viewquest','agree',args=[id,0]) + "' , ['quest'], 'target')")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class="btn btn-success  btn-sm btn-group-sm", _onclick=stringlink, _VALUE="Agree")
        elif action == 'Disagree':
            stringlink = XML("ajax('" + URL('viewquest','agree',args=[id,0]) + "' , ['quest'], 'target')")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class="btn btn-danger  btn-sm btn-group-sm", _onclick=stringlink, _VALUE="Disagree")
        elif action == 'Approve':
            stringlink = XML("ajax('" + URL('answer','quickanswer',args=[id,1]) + "' , ['quest'], 'target')")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class="btn btn-success  btn-sm btn-group-sm", _onclick=stringlink, _VALUE="Approve")
        elif action == 'Disapprove':
            stringlink = XML("ajax('" + URL('answer','quickanswer',args=[id,2]) + "' , ['quest'], 'target')")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class="btn btn-danger  btn-sm btn-group-sm", _onclick=stringlink, _VALUE="Disapprove")
        elif action == 'Edit':
            stringlink = XML("parent.location='" + URL('submit','new_question',args=['quest',id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Edit")
        elif action == 'Next_Action':
            stringlink = XML("parent.location='" + URL('answer','get_question',args=['action'], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Next Action")
        elif action == 'Next_Issue':
            stringlink = XML("parent.location='" + URL('answer','get_question',args=['issue'], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Next Issue")
        elif action == 'Next_Question':
            stringlink = XML("parent.location='" + URL('answer','get_question',args=['quest'], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Next Question")
        elif action == 'Create_Action':
            stringlink = XML("parent.location='" + URL('submit','new_question',args=['action'], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Create Action")
        elif action == 'Link_Action':
            stringlink = XML("parent.location='" + URL('submit','new_question',args=['action',id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Linked Action")
        elif action == 'Link_Question':
            stringlink = XML("parent.location='" + URL('submit','new_question',args=['quest',id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Linked Question")
        elif action == 'Link_Issue':
            stringlink = XML("parent.location='" + URL('submit','new_question',args=['issue',id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Linked Issue")
        elif action == 'View':
            stringlink = XML("parent.location='" + URL('viewquest','index',args=[id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="View")
        elif action == 'Link':
            stringlink = XML("ajax('" + URL('event','link',args=[session.eventid, id, 'link']) + "' , ['challreason'], 'target')")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Link")
        elif action == 'Unlink':
            stringlink = XML("ajax('" + URL('event','link',args=[session.eventid, id, 'unlink']) + "' , ['challreason'], 'target')")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Unlink")
        else:
            buttonhtml = XML("<p>Button not setup</p>")

    elif rectype == 'location':
        if action == 'Edit_Location':
            stringlink = XML("parent.location='" + URL('location','index',args=[id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Edit")
        elif action == 'View_Location':
            stringlink = XML("parent.location='" + URL('location','viewlocation',args=[id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="View")
        else:
            buttonhtml = XML("<p>Button not setup</p>")
    elif rectype == 'event':
        if action == 'Add_Event_Location':
            stringlink = XML("parent.location='" + URL('event','new_event',args=[id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Add Event")
        elif action == 'View_Event':
            stringlink = XML("parent.location='" + URL('event','viewevent',args=[id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="View Event")
        elif action == 'Add_Items':
            stringlink = XML("parent.location='" + URL('event','new_event',args=[id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Add Items")
        elif action == 'Edit_Event':
            stringlink = XML("parent.location='" + URL('event','new_event',args=['Not_Set',id], extension='html')+ "'")
            buttonhtml = TAG.INPUT(_TYPE='BUTTON',_class=stdclass, _onclick=stringlink, _VALUE="Edit Event")
        else:
            buttonhtml = XML("<p>Button not setup</p>")
    else:
        buttonhtml = XML("<p>Button not setup</p>")



    return buttonhtml


def get_buttons(qtype, status, resolvemethod,  id, owner, userid, hasanswered=False, context='std'):
    avail_actions = get_actions(qtype, status, resolvemethod, owner, userid, hasanswered, context)
    return butt_html(avail_actions, context, id, 'quest')


def get_locn_buttons(locid, shared, owner, userid, context='std'):
    avail_actions = get_locn_actions(locid, shared, owner, userid, context)
    return butt_html(avail_actions, context, locid, 'location')


def get_event_buttons(eventid, shared, owner, userid, context='std'):
    avail_actions = get_event_actions(eventid, shared, owner, userid, context)
    return butt_html(avail_actions, context, eventid, 'event')


def butt_html(avail_actions,context,id,rectype):
    buttonhtml=False
    for x in avail_actions:
        if buttonhtml:
            buttonhtml += make_button(x, id, context, rectype)
            buttonhtml += '\r'
        else:
            buttonhtml = make_button(x, id, context, rectype)
            buttonhtml += '\r'
    return buttonhtml

def get_locn_actions(locid, shared, owner, userid, context='std'):
    avail_actions=['View_Location']
    if shared is True or owner == userid:
        avail_actions.append('Add_Event_Location')
    if owner == userid:
        avail_actions.append('Edit_Location')
    return avail_actions


def get_event_actions(eventid, shared, owner, userid, context='std'):
    avail_actions=['View_Event']
    if shared is True or owner == userid:
        avail_actions.append('Add_Items')
    if owner == userid:
        avail_actions.append('Edit_Event')
    return avail_actions

