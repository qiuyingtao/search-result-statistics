# coding=utf-8

import os
import sys
import ConfigParser
import time as t
import StringIO
import gzip
import cookielib
import urllib2
import time
#import sqlite3

reload(sys) # Python2.5 初始化后会删除 sys.setdefaultencoding 这个方法，我们需要重新载入   
sys.setdefaultencoding('utf-8') 

def unzip(data):
    data = StringIO.StringIO(data)
    gz = gzip.GzipFile(fileobj=data)
    data = gz.read()
    gz.close()
    return data

def getWebPages(proxy_enable, http_proxy, url, cookie, start_page, end_page):
    cj = cookielib.CookieJar()
    cookie_handler = urllib2.HTTPCookieProcessor(cj)
    
    proxy = urllib2.ProxyHandler({"http" : http_proxy})  
    noProxy = urllib2.ProxyHandler({})  
    
    if proxy_enable == 1:  
        proxy_handler = proxy
    else:  
        proxy_handler = noProxy
    
    opener = urllib2.build_opener(cookie_handler, proxy_handler)
    opener.addheaders = [('Host', 's.weibo.com'), 
                         ('User-Agent', '"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0"'), 
                         ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'), 
                         ('Accept-Language', 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3'), 
                         ('Accept-Encoding', 'gzip, deflate'), 
                         ('DNT', '1'), 
                         ('Cookie', cookie), 
                         ('Connection', 'keep-alive')]
    
    urls = []
    webPageList = []

    if start_page == end_page:
        urls.append(url + '&page=' + str(start_page))
    else:
        for pageNumber in range(start_page, end_page+1):
            urls.append(url + '&page=' + str(pageNumber))
            
    for url in urls:
        try:
            print utf82gbk('\n\n正在获取 ' + url + ' 的内容...')
            response = opener.open(url, timeout = 120)
            htmldata = unzip(response.read())
            #print htmldata
            webPageList.append(htmldata)
            time.sleep(5)
        except:
            print utf82gbk('网络出现错误，如果使用了代理请看代理是否配置正确，同时请确认url和cookie是否填写正确，然后请重新运行程序。若确认网络通畅仍持续出现这个问题，请联系作者')
            sys.exit()
    return webPageList

def analyzeWebPages(webPageList, db_enable):
#    cx = sqlite3.connect('sra.db')
#    cu = cx.cursor()
    lineList = []
    for webPage in webPageList:
        weibo = ''
        dlList = []

        scriptStart = webPage.find('STK && STK.pageletM && STK.pageletM.view({"pid":"pl_wb_feedlist","js"')
        if scriptStart != -1:
            weibo = webPage[scriptStart:]
            scriptEnd = weibo.find('</script>')
            weibo = weibo[:scriptEnd]

        scriptStart = webPage.find('STK && STK.pageletM && STK.pageletM.view({"pid":"pl_weibo_direct","js"')
        if scriptStart != -1:
            weibo = webPage[scriptStart:]
            scriptEnd = weibo.find('</script>')
            weibo = weibo[:scriptEnd]

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
            title = '无'
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
                title = '无'
            #if title == 'n/a':
            #    continue
    
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

#            if (db_enable == 1):
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

http_url = cf.get('http', 'url')
cookie = cf.get('http', 'cookie')
try:
    start_page = cf.getint('http', 'startpage')
except ValueError:
    print utf82gbk('配置文件里的startpage应设为整数')
    sys.exit()
try:
    end_page = cf.getint('http', 'endpage')
except ValueError:
    print utf82gbk('配置文件里的endpage应设为整数')
    sys.exit()

result_path = cf.get('result', 'path')

write_type = cf.get('write', 'type')

try:
    proxy_enable = cf.getint('proxy', 'enable')
except ValueError:
    print utf82gbk('配置文件里的proxy下的enable应设为整数')
    sys.exit()
proxy_host = cf.get('proxy', 'host')
proxy_port = cf.get('proxy', 'port')

#db_enable = cf.getint('db', 'enable')

REWRITE = 'r'
APPEND = 'a'
PROXYENABLE = 1
PROXYDISABLE = 0
DBENABLE = 1
DBDISABLE = 0

baseUrl = ''
if http_url.find('/wb/') != -1:
    referIndex = http_url.find('&Refer')
    if referIndex != -1:
        baseUrl = http_url[0:referIndex]
    else:
        print utf82gbk('搜索链接地址有误！高级搜索时链接地址应该包含Refer，请查看配置文件里是否写错了，如有疑问请联系作者')
        sys.exit()
elif http_url.find('/weibo/') != -1:
    askIndex = http_url.find('?')
    if askIndex != -1:
        baseUrl = http_url[0:askIndex]
    else:
        print utf82gbk('搜索链接地址有误！普通搜索时链接地址应该包含?，请查看配置文件里是否写错了，如有疑问请联系作者')
        sys.exit()
else:
    print utf82gbk('呃。。。这种搜索链接地址是怎么来的？目前还不支持，请联系作者')
    sys.exit()

if len(cookie) == 0:
    print utf82gbk('cookie不能为空，请查看配置文件里是否没有填写cookie')
    sys.exit()
        
if start_page < 1 or start_page > 50:
    print utf82gbk('搜索结果起始页配置写错了，范围应该在1到50之间')
    sys.exit()

if end_page < 1 or end_page > 50:
    print utf82gbk('搜索结果结束页配置写错了，范围应该在1到50之间')
    sys.exit()

if start_page > end_page:
    print utf82gbk('搜索结果起始页应该小于或等于结束页，请查看配置文件里是否写错了')
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

if proxy_enable != PROXYENABLE and proxy_enable != PROXYDISABLE:
    print utf82gbk('是否使用代理的配置写错了，应该是1（使用代理）或者是0（不使用代理）')
    sys.exit()

#if db_enable != DBENABLE and db_enable != DBDISABLE:
#    print utf82gbk('是否使用数据库的配置写错了，应该是1（使用数据库）或者是0（不使用数据库）')
#    sys.exit()

http_proxy = ''
if proxy_enable == PROXYDISABLE:
    http_proxy = ''
else:
    http_proxy = 'http://' + proxy_host + ':' + proxy_port

print utf82gbk('\n############微博搜索结果统计工具############\n')
print utf82gbk('希望这个小工具能让我最亲爱的小表妹王晨别太累\n')
print utf82gbk('作者：邱英涛\n')
print utf82gbk('版本：0.4\n')
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
print 'Enjoy it!\n'

webPageList = getWebPages(proxy_enable, http_proxy, baseUrl, cookie, start_page, end_page)
data = analyzeWebPages(webPageList, DBDISABLE)

try:
    if write_type == REWRITE:
        r = open(result_path, 'w')
        r.write(utf82gbk('昵称,头衔,赞,转发,收藏,评论,日期,时间,链接,内容\n'))
        r.writelines(data)
        r.close()
    
    if write_type == APPEND:
        if os.path.isfile(result_path):
            r = open(result_path, 'a')
            r.writelines(data)
            r.close()
        else:
            r = open(result_path, 'w')
            r.write(utf82gbk('昵称,头衔,赞,转发,收藏,评论,日期,时间,链接,内容\n'))
            r.writelines(data)
            r.close()
    print utf82gbk('统计结果文件生成完毕！请查看 ') + result_path
except IOError:
    print utf82gbk('文件生成失败！文件可能正在被别的编辑器比如Excel之类的使用，请关闭相关编辑器后再试。')