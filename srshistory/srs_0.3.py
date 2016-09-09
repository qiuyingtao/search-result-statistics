# coding=utf-8

import os
import sys
import ConfigParser
import time as t
#import sqlite3

reload(sys) # Python2.5 初始化后会删除 sys.setdefaultencoding 这个方法，我们需要重新载入   
sys.setdefaultencoding('utf-8') 

def analyzeWebPages(webPageFilePathList, db_enable):
#    cx = sqlite3.connect('sra.db')
#    cu = cx.cursor()
    lineList = []
    for webPageFilePath in webPageFilePathList:
        print '\n', webPageFilePath, '\n'
        f = open(webPageFilePath)
        weibo = ''
        dlList = []
        
        for i in f.readlines():
            if i.find('STK && STK.pageletM && STK.pageletM.view({"pid":"pl_wb_feedlist","js"') != -1:
                weibo = i
                break
            if i.find('STK && STK.pageletM && STK.pageletM.view({"pid":"pl_weibo_direct","js"') != -1:
                weibo = i
                break
            
        while True:
            start = weibo.find('<dl class=\\"feed_list W_linecolor')
            if start == -1:
                break
            wbTemp = weibo[start+3:]
            dlStart = wbTemp.find('<dl')
            dlEnd = wbTemp.find('dl>')
            if dlStart < dlEnd:
                wbTemp = wbTemp[dlEnd+3:]
                end = start + 3 + dlEnd + 3 + wbTemp.find('dl>')
            else:
                end = start + 3 + dlEnd
            dl = weibo[start:end+3]
            dlList.append(dl)
            weibo = weibo[end+3:]
        
        for item in dlList:
            #print item
            title = 'n/a'
            trans = item.find('transparent.gif')
            if trans != -1:
                titleTemp = item[trans:]
                titleStart = titleTemp.find('title')
                titleEnd = titleTemp.find('alt')
                title = titleTemp[titleStart+9:titleEnd-3]
            if title == '\\u5fae\\u535a\\u673a\\u6784\\u8ba4\\u8bc1':
                title = '蓝V'
            elif title.find('\\u5fae\\u535a\\u4e2a\\u4eba\\u8ba4\\u8bc1') != -1:
                title = '黄V'
            elif title == '\\u5fae\\u535a\\u8fbe\\u4eba':
                title = '达人'
            comm = item.find('<dl class=\\"comment W_textc W_linecolor W_bgcolor')
            if comm != -1 and comm < trans:
                title = 'n/a'
            if title == 'n/a':
                continue
    
            nicknameStart = item.find('<a nick-name=')
            nicknameEnd = nicknameStart + item[nicknameStart:].find('href=')
            nickname = item[nicknameStart+15:nicknameEnd-3].decode('unicode_escape')

            contentStart = item.find('<em>')
            item = item[contentStart+4:]
            contentEnd = item.find('<\\/em>')
            content = item[:contentEnd+6]
            content = content.replace('\\"', '"').replace("\\/", "/")
            contentTemp = ''
            while True:
                ltIndex = content.find('<')
                if ltIndex == -1 and len(content) == 0:
                    break
                contentTemp = contentTemp + content[:ltIndex]
                gtIndex = content.find('>') 
                content = content[gtIndex+1:]
            content = contentTemp.decode('unicode_escape')
        
            praised = '0'
            emStart = item.find('<em class=\\"W_ico20 icon_praised_b\\">')
            emTemp = item[emStart:]
            praisedEnd = emTemp.find(')')
            ahrefIndex = emTemp.find('<\\/a>')
            if praisedEnd < ahrefIndex:
                praisedStart = emTemp.find('(')
                praised = emTemp[praisedStart+1:praisedEnd]
        
            forward = '0'
            actionStart = item.find('action-type=\\"feed_list_forward')
            actionTemp = item[actionStart:]
            forwardEnd = actionTemp.find(')')
            ahrefIndex = actionTemp.find('<\\/a>')
            if forwardEnd < ahrefIndex:
                forwardStart = actionTemp.find('(')
                forward = actionTemp[forwardStart+1:forwardEnd]
        
            favorite = '0'
            actionStart = item.find('action-type=\\"feed_list_favorite')
            actionTemp = item[actionStart:]
            favoriteEnd = actionTemp.find(')')
            ahrefIndex = actionTemp.find('<\\/a>')
            if favoriteEnd < ahrefIndex:
                favoriteStart = actionTemp.find('(')
                favorite = actionTemp[favoriteStart+1:favoriteEnd]
        
            comment = '0'
            actionStart = item.find('action-type=\\"feed_list_comment')
            actionTemp = item[actionStart:]
            commentEnd = actionTemp.find(')')
            if commentEnd != -1:
                ahrefIndex = actionTemp.find('<\\/a>')
                if commentEnd < ahrefIndex:
                    commentStart = actionTemp.find('(')
                    comment = actionTemp[commentStart+1:commentEnd]
        
            dateIndex = actionTemp.find('date=')
            datetime = actionTemp[dateIndex+7:dateIndex+17]
            datespacetime = t.strftime('%Y-%m-%d %X', t.localtime(int(datetime)))
            dateAndTime = datespacetime.split(' ')
            date = dateAndTime[0]
            time = dateAndTime[1]

            linkStart = actionTemp.find('<a href')
            linkEnd = actionTemp.find('title')
            link = actionTemp[linkStart+10:linkEnd-3]
            link = link.replace('\\/', '/')
        
            #print '昵称：%s\t头衔：%s\t赞：%s\t转发：%s\t收藏：%s\t评论：%s\t日期：%s\t时间：%s' % (nickname, title, praised, forward, favorite, comment, date, time)
            line =  '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (nickname, title, praised, forward, favorite, comment, date, time, link, content)
            try:
                print line
            except UnicodeEncodeError:
                pass
            lineList.append(utf82gbk(line))

#            if (db_enable == 'y'):
#                sqlStr = 'INSERT INTO metaweibo (nickname, title, praised, forward, favorite, comment, date, time, datetime) VALUES ("%s", "%s", %s, %s, %s, %s, "%s", "%s", %s)' % (nickname, title, int(praised), int(forward), int(favorite), int(comment), date, time, int(datetime))
#                cu.execute(sqlStr)
#    cx.commit()
#    cx.close()
    return lineList

def utf82gbk(txt):
    postTxt = ''
    try:
        postTxt = txt.decode('utf-8').encode('gbk')
    except UnicodeEncodeError:
        pass
    return postTxt

cf = ConfigParser.ConfigParser()
cf.read('config.ini')
webpage_path = cf.get('webpage', 'path')
result_path = cf.get('result', 'path')
write_type = cf.get('write', 'type')
#db_enable = cf.get('db', 'enable')
REWRITE = 'r'
APPEND = 'a'
ENABLE = 'y'
DISABLE = 'n'

if os.path.exists(webpage_path) == False:
    print utf82gbk('存放网页的文件夹不存在，请查看配置文件里是否写错了')
    sys.exit()

if result_path[-4:] != '.csv':
    print utf82gbk('统计结果文件名应以.csv结尾，请查看配置文件里是否写错了')
    sys.exit()

dn = os.path.dirname(result_path)
if os.path.exists(dn) == False:
    print utf82gbk('存放统计结果的文件夹不存在，请查看配置文件里是否写错了')
    sys.exit()

if write_type != REWRITE and write_type != APPEND:
    print utf82gbk('生成文件的方式写错了，应该是r（重新生成新文件）或者是a（给已有文件添加新结果）')
    sys.exit()

#if db_enable != ENABLE and db_enable != DISABLE:
#    print utf82gbk('是否使用数据库的配置写错了，应该是y（使用数据库）或者是n（不使用数据库）')
#    sys.exit()

webPageFilePathList = []
webPageFiles = os.listdir(webpage_path)  
for webPageFile in webPageFiles:  
    webPageFilePathList.append(webpage_path + '/' + webPageFile)

if len(webPageFilePathList) == 0:
    print utf82gbk('存放网页的文件夹下没有文件，请查看配置文件里是否写错了')
    sys.exit()

try:
    print utf82gbk('\n############微博搜索结果统计工具############\n')
    print utf82gbk('希望这个小工具能让我最亲爱的小表妹王晨别太累\n')
    print utf82gbk('作者：邱英涛\n')
    print utf82gbk('版本：0.3\n')
    print utf82gbk('###########################################\n')
    print '5'
    t.sleep(1)
    print '4'
    t.sleep(1)
    print '3'
    t.sleep(1)
    print '2'
    t.sleep(1)
    print '1\n'
    t.sleep(1)

    if write_type == REWRITE:
        r = open(result_path, 'w')
        r.write(utf82gbk('昵称,头衔,赞,转发,收藏,评论,日期,时间,链接,内容\n'))
        r.writelines(analyzeWebPages(webPageFilePathList, DISABLE))
        r.close()
    
    if write_type == APPEND:
        if os.path.isfile(result_path):
            r = open(result_path, 'a')
            r.writelines(analyzeWebPages(webPageFilePathList, DISABLE))
            r.close()
        else:
            r = open(result_path, 'w')
            r.write(utf82gbk('昵称,头衔,赞,转发,收藏,评论,日期,时间,链接,内容\n'))
            r.writelines(analyzeWebPages(webPageFilePathList, DISABLE))
            r.close()
    print utf82gbk('统计结果文件生成完毕！请查看 ') + result_path
except IOError:
    print utf82gbk('文件生成失败！文件可能正在被别的编辑器比如Excel之类的使用，请关闭相关编辑器后再试。')