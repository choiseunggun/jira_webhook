import json
import time

import requests
import logging

from fastapi import Body, FastAPI

app = FastAPI()
jira_url = "http://jira.future.co.kr/browse/"
before_webhookEvent = ''

# create logger for prd_ci
log = logging.getLogger()
log.setLevel(level=logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(lineno)d - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(level=logging.INFO)
ch.setFormatter(formatter)

log.addHandler(ch)

@app.post("/")
async  def web_hook(payload: dict = Body(...)):
    global before_webhookEvent

    slack_msg_content = ''
    slack_msg_header = ''
    slack_msg_type = ''
    # log.info(payload)
    json_val = json.dumps(payload)
    log.info('json_val : '+json_val)

    log.info("webhookEvent : "+payload.get("webhookEvent"))
    log.info("before_webhookEvent : "+before_webhookEvent)

    if(payload.get("webhookEvent") == before_webhookEvent == "jira:issue_updated"):
        log.critical("======================================")
        # return

    if(not before_webhookEvent):
        before_webhookEvent = payload.get("webhookEvent")

    try:
        # log.info("issue.key : "+payload.get("issue").get("key"))
        # log.info("issue.fields.status.name : "+payload.get("issue").get("fields").get("status").get("name"))
        # log.info("issue.fields.summary : "+payload.get("issue").get("fields").get("summary"))

        slack_msg_header = '<'+jira_url+payload.get("issue").get("key")+'|*'+payload.get("issue").get("key")+'*>'
        slack_msg_header += '     `'+payload.get("issue").get("fields").get("status").get("name")+'`'
        slack_msg_header += '     *'+payload.get("issue").get("fields").get("summary")+'*'

        # log.info('slack_msg_header : '+slack_msg_header)

        # log.info("issue.fields.project.key : "+payload.get("issue").get("fields").get("project").get("key"))
        # log.info("issue.fields.project.name : "+payload.get("issue").get("fields").get("project").get("name"))
        # log.info("issue.fields.issuetype.name : "+payload.get("issue").get("fields").get("issuetype").get("name"))
        # log.info("issue.fields.assignee.name : "+payload.get("issue").get("fields").get("assignee").get("name"))

        slack_msg_content = 'project : '+payload.get("issue").get("fields").get("project").get("key")
        slack_msg_content += '     Type : '+payload.get("issue").get("fields").get("issuetype").get("name")
        slack_msg_content += '     Priority : '+payload.get("issue").get("fields").get("priority").get("name")
        slack_msg_content += '     담당자 : '+payload.get("issue").get("fields").get("assignee").get("displayName")+"("+\
                             payload.get("issue").get("fields").get("assignee").get("name")+")"

        # log.info('slack_msg_content : '+slack_msg_content)

    except Exception as e:
        log.error(e)

    if(before_webhookEvent == "jira:issue_created"): #이슈 생성
        slack_msg_type = '>jira 이슈 생성'
        slack_msg_type += '\\n>'+payload.get("issue").get("fields").get("summary")
    elif(before_webhookEvent == "jira:issue_updated"): #이슈 수정
        try:
            slack_msg_type = '>jira 이슈 수정 > '+payload.get("changelog").get("items")[0].get("field")
            if(payload.get("changelog").get("items")[0].get("field") == 'description'):
                dash = '\\n'
            elif(payload.get("changelog").get("items")[0].get("field") == '진행 상황(WBSGantt)'):
                log.error("bypass > 진행 상황(WBSGantt)")
                return
            else:
                dash = ' : '
            slack_msg_type += '\\n>수정 전'+dash+str(payload.get("changelog").get("items")[0].get("fromString")).replace("\"","\\\"")
            slack_msg_type += '\\n>수정 후'+dash+str(payload.get("changelog").get("items")[0].get("toString")).replace("\"","\\\"")
        except Exception as e:
            log.error(e)
            slack_msg_type = '>jira 이슈 수정'
    elif(before_webhookEvent == "jira:issue_deleted"): #이슈 삭제
        slack_msg_type = '>jira 이슈 삭제'
    elif(before_webhookEvent == "comment_created"): #댓글 추가
        slack_msg_type = '>jira 이슈 댓글 추가'
        slack_msg_type += '\\n>comment : '+payload.get("comment").get("body").replace("\"","\\\"")
    elif(before_webhookEvent == "comment_updated"): #댓글 수정
        slack_msg_type = '>jira 이슈 댓글 수정'
        slack_msg_type += '\\n>comment : '+payload.get("comment").get("body").replace("\"","\\\"")
    elif(before_webhookEvent == "comment_deleted"): #댓글 삭제
        slack_msg_type = '>jira 이슈 댓글 삭제'

    log.info(slack_msg_type)

    if(slack_msg_header):
        log.info(slack_msg_header)
        slack_msg = "{\"text\": \"[jira 알림] - "+slack_msg_type[:40]+"\","
        slack_msg += "\"blocks\": [{\"type\": \"section\",\"text\": {\"type\": \"mrkdwn\",\"text\": "
        slack_msg += "\""+slack_msg_header+"\\n\\n"+slack_msg_content+"\\n"+slack_msg_type+"\"}}]}"
        log.info(slack_msg)

        url = 'https://hooks.slack.com/services/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'

        x = requests.post(url, data=slack_msg.encode("utf-8"))
        log.info(x)

    before_webhookEvent = payload.get("webhookEvent")
    return


