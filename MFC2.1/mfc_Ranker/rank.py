from aqt.reviewer import Reviewer
from aqt.toolbar import Toolbar 
from anki.hooks import wrap, runFilter, runHook, addHook
from anki.sound import playFromText, clearAudioQueue
from aqt.utils import tooltip, shortcut, askUser
from aqt import utils
from aqt.main import AnkiQt
from aqt.overview import Overview
from anki.db import DB
import time
from aqt.qt import *
import sqlite3
import os, sys
from anki.storage import Collection
from anki.utils import stripHTML, json
import time
import logging
from copy import deepcopy
from aqt import mw
from aqt.utils import showInfo, tooltip
import os
import sys
import datetime
import gzip
pathList = sys.path

address = "https://www.medicflashcards.com/"
baddress = "http://localhost:5000/"

# user choices ! 
MANUAL_RANK_FILTER_CHOICE = None
REPEATS_UNTILL_ACTION = 2

# minutes
IDLE_PERIOD = 10
RETRY_PERIOD = 1



path = mw.pm.base
RANK_DATABASE = path + "/rank.db"

def setDbs():
	onload = mw.pm.profileFolder(create=False)
	ANKI_DATABASE = str(onload) + "/collection.anki2"
	ANKI_DATABASE_zip =str(onload) + "/collection.anki2.gz"
	LOCAL_DB = str(onload) + '/collection.anki2'
	LOCAL_MEDIA_DB = str(onload) +  'collection.media/%s'
	LOCAL_DB_PREV = str(onload) + '/collection-prev.anki2'
	return(ANKI_DATABASE,ANKI_DATABASE_zip,LOCAL_DB,LOCAL_MEDIA_DB,LOCAL_DB_PREV)

import zipfile
requestfile = path.split("/")
paths = sys.path
path = paths[-1]
for path in paths:
	if "addons" in path:
		requestfi = path + "/mfc_Ranker/modules"
sys.path.append(requestfi)
# showInfo(requestfi)
import requests
from requests.auth import HTTPBasicAuth

conn = sqlite3.connect(RANK_DATABASE)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS rankingSystem (time INTEGER PRIMARY KEY autoincrement, cid INTEGER , rank INTEGER)""")
conn.commit()
c.execute("""CREATE TABLE IF NOT EXISTS overallRanking (cid INTEGER UNIQUE, overallRank INTEGER, times INTEGER, timesync INTEGER)""")
conn.commit()
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS tokens (id INTEGER PRIMARY KEY autoincrement, token varchar(128), last_seen DATETIME, online_rank INTEGER )""")
conn.commit()
b = c.execute("""PRAGMA table_info(tokens);""")
lengethcol = len(b.fetchall())
if lengethcol != 4:
	try:
		c.execute("""ALTER TABLE tokens ADD COLUMN online_rank INTEGER;""")
		conn.commit()
	except sqlite3.OperationalError:
		pass
conn.close()


conn.close()



def showRank(self):
	self.state = "rank"
	showRankButtons(self)

# Answering a card, answerCard = answerRank, answerButton = answerRankButton
############################################################
def _showEaseButtons(self):
	showRank(self)

def _showNewEaseButtons(self):
	self.bottom.web.setFocus()
	middle = self._answerButtons()
	self.bottom.web.eval("showAnswer(%s);" % json.dumps(middle))

def _answerRank(self, rank):
	if rank == 1:
		rank = 0
	if rank == 2:
		rank = 50
	if rank == 3:
		rank = 100

	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()
	id =  self.card.id
	curtime = int(time.time())*1000
	c.execute("""INSERT INTO rankingSystem VALUES (? ,?,?) """, (curtime, id, rank))
	conn.commit()
	
	c.execute("""SELECT rank FROM rankingSystem WHERE cid = ?""", (self.card.id,))
	allCards = c.fetchall()
	c.execute("""SELECT timesync FROM overallRanking WHERE cid = ?""", (self.card.id,))
	timesync = c.fetchone()
	try:
		timesyn = int(timesync[0])
		timesyn += 1 
	except:
		timesyn = 1

	rankForCid = []
	for i in allCards:
		rankForCid.append(float(i[0]))
	
	leng = len(rankForCid)
	avg = sum(rankForCid) / leng
	
	c.execute("""INSERT OR REPLACE INTO overallRanking VALUES (?, ?, ?, ?)""", (self.card.id, avg, leng, timesyn))
	conn.commit()
	conn.close()

	self.mw.autosave()
	self.state = "answer"
	_showNewEaseButtons(self)

def adjustSched(self):
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()
	
	
	if not self.card:
		self.mw.reset()
		self.mw.moveToState("overview")
		return
	
	c.execute("""SELECT times FROM overallRanking WHERE cid = ?""", (self.card.id,))
	times = c.fetchone()
	c.execute("""SELECT overallRank FROM overallRanking WHERE cid = ?""", (self.card.id,))
	rank = c.fetchone()

	try:
		if times[0] > REPEATS_UNTILL_ACTION and rank[0] < RANK_FILTER_CHOICE:
			# self.mw.checkpoint(_("Suspend"))
			self.mw.col.sched.suspendCards([self.card.id])
			self.mw.reset()
			self.nextCard()
			adjustSched(self)
		else:
			self.nextCard()
	except TypeError:
		self.nextCard()


def showRankButtons(self):
	middle = answerRankButtons()
	self.bottom.web.eval("showAnswer(%s);" % json.dumps(middle))


answerRankButtonList = ((1, ("No Need")), (2, ("Need")), (3, ("Vital")))


# answerButtons = answerRankButtons
def answerRankButtons():
	#    default = self._defaultEase()
	def but(i, label):
		if i == 2:
			extra = "id=defease"
		else:
			extra = ""
		
		return '''
			<td align=center><div class=spacer></div><button %s title="%s" onclick='pycmd("rank%d");'>%s</button></td>''' % (extra, _("Shortcut key: %s") % i, i, label)
	buf = "<center><table cellpading=0 cellspacing=0><tr>"
	for i, label in answerRankButtonList:
		buf += but(i, label) # change buf to but
	buf += "</tr></table>"  # change buf to but
	script = """<script>$(function () { $("#defease").focus(); });</script>"""
	return buf + script


def _answerCard(self, ease):
	"Reschedule card and show next."
	if self.mw.state != "review":
		# showing resetRequired screen; ignore key
		return
	if self.state != "answer":
		return
	if self.mw.col.sched.answerButtons(self.card) < ease:
		return
	self.mw.col.sched.answerCard(self.card, ease)
	self._answeredIds.append(self.card.id)
	self.mw.autosave()
	self.nextCard()


def linkHandler(self, url, _old):
	if url.startswith("rank"):
		_answerRank(self, int(url[4:]))
	return _old(self, url)

def newLinkHandler(self, url):
		if url.startswith("rank"):
			_answerRank(self, int(url[4:]))



def review_link_handler_wrapper(reviewer, url):
	"""Play the sound or call the original link handler."""
	if url.startswith("rank"):
		_answerRank(self, int(url[4:]))
	else:
		original_review_link_handler(reviewer, url)


def simple_link_handler(url):
	"""Play the file."""
	if url.startswith("rank"):
		_answerRank(self, int(url[4:]))
	else:
		QDesktopServices.openUrl(QUrl(url))

def add_preview_link_handler(browser):
	"""Make sure we play the files from the preview window."""
	browser._previewWeb.setLinkHandler(simple_link_handler)

def keyHandler(self, evt):
	key = str(evt)
	if key in ["1", "2", "3", "4"]:
		isr = self.state == "rank"
			#if isr:
			#self._showAnswerHack()
		if key == "1":
			if isr:
				_answerRank(self, 1)
			else:
				self._answerCard(1)
		elif key == "2":
			if isr:
				_answerRank(self, 2)
			else:
				self._answerCard(2)
		elif key == "3":
			if isr:
				_answerRank(self, 3)
			else:
				self._answerCard(3)
		elif key == r"/ ":
			if isr:
				_answerRank(self, 2)
			else:
				self._answerCard(2)
		elif key == r"4":
			self._answerCard(4)
		else:
			return self,evt
	else:
		return self, evt

def shortcutKeys(self):
		return [
			("e", self.mw.onEditCurrent),
			(" ", self.onEnterKey),
			(Qt.Key_Return, self.onEnterKey),
			(Qt.Key_Enter, self.onEnterKey),
			("r", self.replayAudio),
			(Qt.Key_F5, self.replayAudio),
			("Ctrl+1", lambda: self.setFlag(1)),
			("Ctrl+2", lambda: self.setFlag(2)),
			("Ctrl+3", lambda: self.setFlag(3)),
			("Ctrl+4", lambda: self.setFlag(4)),
			("*", self.onMark),
			("=", self.onBuryNote),
			("-", self.onBuryCard),
			("!", self.onSuspend),
			("@", self.onSuspendCard),
			("Ctrl+Delete", self.onDelete),
			("v", self.onReplayRecorded),
			("Shift+v", self.onRecordVoice),
			("o", self.onOptions),
			("1", lambda: keyHandler(self,1)),
			("2", lambda: keyHandler(self,2)),
			("3", lambda: keyHandler(self,3)),
			("4", lambda: keyHandler(self,4)),
		]


def onEnterKey(self):
	if self.state == "question":
		self._getTypedAnswer()
	elif self.state == "rank":
		_answerRank(self,2)
	elif self.state == "answer":
		self.bottom.web.evalWithCallback("selectedAnswerButton()", self._onAnswerButton)



def newOpenLink(link):
	with noBundledLibs():
		QDesktopServices.openUrl(QUrl(link))



def mySetupButtons(self, _old):
	# buttons = origSetupButtons(self)
	ret = _old(self)
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()

	c.execute("""SELECT overallRank FROM overallRanking WHERE cid = ?""", (self.card.id,))
	rank = c.fetchone()
	num = round(rank[0])
	alabel = str(int(num))

	strr ="<div style='float:right; padding-bottom:5px;top:10px; right:10px; position:fixed;'>Rank:%s</div>" % alabel
	button = strr + ret
	return button

# Reviewer._linkHandler = newLinkHandler
Reviewer._linkHandler = wrap(Reviewer._linkHandler,newLinkHandler, "before")
Reviewer._shortcutKeys = shortcutKeys
Reviewer._answerCard =_answerCard
Reviewer._showEaseButtons = _showEaseButtons
Reviewer.onEnterKey = onEnterKey

utils.openLink = wrap(utils.openLink,newOpenLink, "around")
Reviewer._answerButtons = wrap(Reviewer._answerButtons,mySetupButtons,"around")

class FlashCardWindow(QWidget):

	def __init__(self):
		super(FlashCardWindow, self).__init__()

		self.results = None
		self.thread = None

		self.initGUI()

	# create GUI skeleton
	def initGUI(self):
		
		self.box_top = QVBoxLayout()
		self.box_upper = QHBoxLayout()

		# left side
		self.box_left = QVBoxLayout()

		# username 
		self.box_name = QHBoxLayout()
		self.label_url = QLabel("Username:")
		self.text_username = QLineEdit("",self)
		self.text_username.setMinimumWidth(300)

		self.box_name.addWidget(self.label_url)
		self.box_name.addWidget(self.text_username)

		# add layouts to left
		self.box_left.addLayout(self.box_name)
### -   password
		self.box_name = QHBoxLayout()
		self.label_url = QLabel("Password:")
		self.text_password = QLineEdit("",self)
		self.text_password.setMinimumWidth(300)

		self.box_name.addWidget(self.label_url)
		self.box_name.addWidget(self.text_password)

		# add layouts to left
		self.box_left.addLayout(self.box_name)
###
		# right side
		self.box_right = QVBoxLayout()

		# code (import set) button
		self.box_code = QHBoxLayout()
		self.button_code = QPushButton("Connect", self)
		self.box_code.addStretch(1)
		self.box_code.addWidget(self.button_code)
		self.button_code.clicked.connect(self.onCode)

		self.buttonbutbut = QHBoxLayout()
		self.upload_but = QPushButton("Upload Collection", self)
		self.buttonbutbut.addWidget(self.upload_but)
		self.upload_but.clicked.connect(self.uploadBut)

		self.download_but = QPushButton("Download Collection", self)
		self.buttonbutbut.addWidget(self.download_but)
		self.download_but.clicked.connect(self.downloadBut)

		self.media_sync = QPushButton("Sync Media", self)
		self.buttonbutbut.addWidget(self.media_sync)
		self.media_sync.clicked.connect(self.media_sync_but)


		self.box_left.addLayout(self.buttonbutbut)
		# add layouts to right
		self.box_right.addLayout(self.box_code)
		
		# add left and right layouts to upper
		self.box_upper.addLayout(self.box_left)
		self.box_upper.addSpacing(20)
		self.box_upper.addLayout(self.box_right)

		# results label
		self.label_results = QLabel("\r\n<i>Use the same username and password from medicflashcards to be able to sync</i>")

		# add all widgets to top layout
		self.box_top.addLayout(self.box_upper)
		self.box_top.addWidget(self.label_results)
		self.box_top.addStretch(1)
		self.setLayout(self.box_top)

		# go, baby go!
		self.setMinimumWidth(500)
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		self.setWindowTitle("Medic Flashcard connection setup")
		self.show()

	def media_sync_but(self):
		self.label_results.setText("We are currently syncing your media files, you will be notified when it is completed.")
		syncMedia()

	def downloadBut(self):
		self.label_results.setText("We've downloded your online collection. \n Restart Anki to view new decks.")
		downloadFromMFC()

	def uploadBut(self):
		self.label_results.setText("We've started uploading your collection. \n Remember: we will upload your collection automatically after 5 minutes of inactivity.")
		uploadToMFC()

	def onCode(self):
		self.label_results.setText("Waiting...")
		# grab input
		username = self.text_username.text()
		password = self.text_password.text()
		if username == "" or password == "":
			self.label_results.setText("Oops! You forgot to put in a username or password!")

		url = address+'api/token'

		s = requests.Session()
		r = s.get(url, auth=HTTPBasicAuth(username, password))
		self.label_results.setText("We've after securely!")

		response = json.loads(r.content)
		token = response['token']
		setLocalLastToken(token)
		self.label_results.setText("We've connected securely!")

def removeCardsOutOfRange():
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()

	c.execute("""SELECT * FROM overallRanking""")
	rankList = c.fetchall()
	cidList = []
	unsuspend_cidList = []
	for i in rankList:
		cid, orank, times, timesync = i
		if orank < RANK_FILTER_CHOICE and  times > REPEATS_UNTILL_ACTION:
			cidList.append(cid)
		else:
			unsuspend_cidList.append(cid)
	conn.close()
	mw.col.sched.suspendCards(cidList)
	mw.reset()
	mw.col.sched.unsuspendCards(unsuspend_cidList)
	mw.reset()

def media_sync_complete():
	showInfo("Successfully Synced your media files")

@pyqtSlot()
def syncMedia():
	trip = mw.col.media.check()
	worker = ProcessRunnable(sync_media, trip)
	worker.signals.finished.connect(media_sync_complete)
	worker.start()

def sync_media(trip):
	files = setDbs()#    (ANKI_DATABASE | ANKI_DATABASE_zip | LOCAL_DB | LOCAL_MEDIA_DB | LOCAL_DB_PREV)
	LOCAL_MEDIA_DB=files[3]
	(nohave, unused, warnings) = trip

	missingList = []
	if nohave:
		for i in nohave:
			missingList.append(i)
	allFiles = []
	for a, b, files in os.walk(LOCAL_MEDIA_DB):  
		for i in files:
			allFiles.append(i)

	listoflists = [missingList,allFiles]
	listoflists = json.dumps(listoflists)

	url = address+'api/mediasynccheck'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		r = s.post(url, data=listoflists, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		response = json.loads(r.content)
		needUpload = response[0]
		needDownload = response[1]

		for i in needUpload:
			uploadURL = address + 'api/uploadMedia'
			files = {'photo': open(LOCAL_MEDIA_DB % str(i), 'rb')}
			r = s.post(uploadURL, files=files)
		for i in needDownload:
			url = address +'static/collection.media/%s' % str(i)
			response = requests.get(url)
			if r.status_code == 200:
				with open(LOCAL_MEDIA_DB %str(i), 'wb') as f:
					f.write(response.content)

def syncRanks():
	# upload rank db
	files = {'file': open(RANK_DATABASE,'rb')}
	url = address + 'api/uploadranks'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		r = s.get(url, files=files, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		conn = sqlite3.connect(RANK_DATABASE)
		c = conn.cursor()

		# update local db with valesn

		try:
			response = json.loads(r.content)
			ranklist = response['rank_list']
			for item in ranklist:
				try:
					c.execute('INSERT OR REPLACE INTO rankingSystem VALUES (?,?,?)', item)
					conn.commit()
				except sqlite3.IntegrityError:
					pass
		except ValueError:# meaning theres nothign to update
			pass
		c.execute("""UPDATE overallRanking SET timesync = 0""")
		conn.commit()
		conn.close()

def thread_complete():
	showInfo("Downloaded, please restart Anki.")

@pyqtSlot()
def downloadFromMFC():
	worker = ProcessRunnable(target=downloading)
	worker.signals.finished.connect(thread_complete)
	worker.start()

def downloading():
	files = setDbs()#    (ANKI_DATABASE | ANKI_DATABASE_zip | LOCAL_DB | LOCAL_MEDIA_DB | LOCAL_DB_PREV)
	ANKI_DATABASE_zip=files[1]
	LOCAL_DB=files[2]
# create backup
# overwrite local collectiion
# currently checks for each media, send media list instead and check on server end
	# os.rename(LOCAL_DB,LOCAL_DB_PREV)
	url = address + 'api/downloadsync'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		r = s.get(url, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		if r.status_code != 200:
			showInfo("Whoops, we had a problem connecting: Status Code %s" % r.status_code)
		else:
			with open(ANKI_DATABASE_zip, 'wb') as f:  
				f.write(r.content)
			inF = gzip.open(ANKI_DATABASE_zip, 'rb')
			outF = open(LOCAL_DB, 'wb')
			outF.write( inF.read() )
			inF.close()
			outF.close()
			os.remove(LOCAL_DB+"-wal")
			os.remove(LOCAL_DB+"-shm")
			# tooltip("Downloaded! Restart anki to view changes!")

		# tooltip("Getting media..")
		# syncMedia()
		syncRanks() 
	


def ManualDownload():
	mw.progress.start(label="Downloading from medicflashcards.com....\n Please don't close Anki \n (This can take up to 30 seconds!)", immediate=True)
	files = setDbs()#    (ANKI_DATABASE | ANKI_DATABASE_zip | LOCAL_DB | LOCAL_MEDIA_DB | LOCAL_DB_PREV)
	ANKI_DATABASE_zip=files[1]
	LOCAL_DB=files[2]
# create backup
# overwrite local collectiion
# currently checks for each media, send media list instead and check on server end
	# os.rename(LOCAL_DB,LOCAL_DB_PREV)
	url = address + 'api/downloadsync'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		r = s.get(url, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		if r.status_code != 200:
			showInfo("Whoops, we had a problem connecting: Status Code %s" % r.status_code)
		else:
			with open(ANKI_DATABASE_zip, 'wb') as f:  
				f.write(r.content)
			tooltip("Downloaded! Restart anki to view changes!")

		tooltip("Getting media..")
		# syncMedia()
		syncRanks() 
		showInfo("Downloaded! Restart Anki to see your downloaded collection")
	mw.progress.finish()

class WorkerSignals(QObject):
	finished = pyqtSignal()
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progress = pyqtSignal(int)

class ProcessRunnable(QRunnable):
	"""
	Only used to build the index in background atm.
	"""
	def __init__(self, target, *args):
		QRunnable.__init__(self)
		self.t = target
		self.args = args
		self.signals = WorkerSignals()

	@pyqtSlot()
	def run(self):
		try:
			self.t(*self.args)
		finally:
			self.signals.finished.emit()
		# QThreadPool.waitForDone()

	def start(self):
		QThreadPool.globalInstance().start(self)

def reloadcollection():
	mw.loadCollection()
	mw.progress.finish()
	showInfo("Uploaded Successfully")

@pyqtSlot()
def uploadToMFC():
	mw._unloadCollection()
	mw.progress.start(label="Uploading to medicflashcards.com....\n Please don't close Anki \n (This can take up to 30 seconds!)", immediate=True)
	worker = ProcessRunnable(target=uploading)
	worker.signals.finished.connect(reloadcollection)
	worker.start()

def uploading():
	files = setDbs()#    (ANKI_DATABASE | ANKI_DATABASE_zip | LOCAL_DB | LOCAL_MEDIA_DB | LOCAL_DB_PREV)
	ANKI_DATABASE_zip=files[1]
	LOCAL_DB=files[2]

# send local collection
# currently checks for media files, should upload list of file names then respond with missing
# upload rank db, gets a list of ranking 


# send local collection
	# mw.progress.start(label="Uploading to medicflashcards.com.... \n (This can take up to 30 seconds!)", immediate=True)
	# mw.col.db.close()
	with open(LOCAL_DB, 'rb') as f_in, gzip.open(ANKI_DATABASE_zip, 'wb') as f_out:
		f_out.writelines(f_in)
	files = {'file': open(ANKI_DATABASE_zip,'rb')}
	url = address+'api/uploadsync'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		r = s.post(url, files=files, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		cpath = mw.pm.collectionPath()
		
		# syncMedia()
		syncRanks()      
	# tooltip("done!")
	# mw.progress.finish()
def ManualUpload():
	files = setDbs()#    (ANKI_DATABASE | ANKI_DATABASE_zip | LOCAL_DB | LOCAL_MEDIA_DB | LOCAL_DB_PREV)
	ANKI_DATABASE_zip=files[1]
	LOCAL_DB=files[2]
	mw._unloadCollection()
# send local collection
# currently checks for media files, should upload list of file names then respond with missing
# upload rank db, gets a list of ranking 
# send local collection
	mw.progress.start(label="Uploading to medicflashcards.com.... \n (This can take up to 30 seconds!)", immediate=True)
	with open(LOCAL_DB, 'rb') as f_in, gzip.open(ANKI_DATABASE_zip, 'wb') as f_out:
		f_out.writelines(f_in)
	files = {'file': open(ANKI_DATABASE_zip,'rb')}
	url = address+'api/uploadsync'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		r = s.post(url, files=files, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		mw.progress.update(_("Gathering Collection..."))
		if r.status_code != 200:
			showInfo("Whoops, we had a problem connecting: Status Code %s" % r.status_code)
		else:
		   pass
		mw.progress.update(_("Syncing Media..."))

		# DISABLED MEDIA SYNC ON UPLOAD BECAUSE IT'S A BIT SLOW  

		# syncMedia()
		# mw.progress.update(_("Syncing Ranks..."))
		syncRanks()      
		tooltip("done!")
	else:
		tooltip("Couldn't connect to database, Unauthorised token")
	mw.progress.finish()
	mw.loadCollection()

def tokenizedAuth():
	#  use by initializing, and indexing the 0 and 1 value for user + pswd
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()
	c.execute("""SELECT token FROM tokens WHERE id = 1""")
	token = c.fetchone()
	conn.close()
	try:
		auth = (str(token[0]),"")
	except TypeError:
		auth = False
	return auth

def onlineLast():
	url = address+'api/updateTimeLastUsed'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		try:
			r = s.post(url, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		except Exception as e:
			showInfo("We couldn't connect to MFC \n\nError ref:%s"%str(e))
			return ""
		if r.status_code != 200:
			if r.status_code == 401:
				showInfo("Connect to medicflashcards to dismiss this message\nTo do this, go to Tools > Medic Flashcards, and entering your account details.")
			else:
				showInfo("It looks like your token expired! This means we coulnd't syncronise with the server. \n\nPlease reconnect by going to Tools > Medic Flashcards. \nStatus code: %s" % str(r.status_code))
			return ""
		else:
			response = json.loads(r.content)
			timess = response['user_seen']
			timess = str(timess)
			new = timess.split('.')
			del new[-1]
			datess = new[0]
			datess = datetime.datetime.strptime(datess, "%Y-%m-%d %H:%M:%S")
			return datess
	else:
		return ""

def setLocalLastToken(token):
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()
	c.execute("""SELECT id FROM tokens WHERE id = 1""")
	val = c.fetchone()
	if val != None:
		c.execute("""UPDATE tokens SET token = ?, last_seen = ? WHERE id = 1""",(str(token),datetime.datetime.now(),))
	else:
		c.execute("""INSERT INTO tokens VALUES (?, ?, ?, ?)""",(1, str(token),datetime.datetime.now(),0))
	conn.commit()
	conn.close()

def setLocalLast():
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()
	c.execute("""SELECT id FROM tokens WHERE id = 1""")
	val = c.fetchone()
	if val != None:
		c.execute("""UPDATE tokens SET last_seen = ? WHERE id = 1""",(datetime.datetime.now(),))
	else:
		pass
	conn.commit()
	conn.close()

def localLast():
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()
	c.execute("""SELECT last_seen FROM tokens WHERE id = 1""")
	lastSeenLocal = c.fetchone()
	if lastSeenLocal != None:
		lastSeenLocal = lastSeenLocal[0]
	conn.close()
	timess = str(lastSeenLocal)
	new = timess.split('.')
	del new[-1]
	try:
		datess = new[0]
		datess = datetime.datetime.strptime(datess, "%Y-%m-%d %H:%M:%S")
	except IndexError:
		datess = 0
	return datess

def downloadZipCheck():
	files = setDbs()#    (ANKI_DATABASE | ANKI_DATABASE_zip | LOCAL_DB | LOCAL_MEDIA_DB | LOCAL_DB_PREV)
	ANKI_DATABASE_zip=files[1]
	LOCAL_DB=files[2]
	if os.path.exists(ANKI_DATABASE_zip):
		inF = gzip.open(ANKI_DATABASE_zip, 'rb')
		os.remove(LOCAL_DB)
		outF = open(LOCAL_DB, 'wb')
		outF.write( inF.read() )
		inF.close()
		outF.close()
		# os.remove(LOCAL_DB+"-wal")
		# os.remove(LOCAL_DB+"-shm")
		os.remove(ANKI_DATABASE_zip)

def newShow():
	from datetime import datetime, timedelta
	lastSeenLocal =  localLast()
	lastSeenOnline = onlineLast()
	files = setDbs()#    (ANKI_DATABASE | ANKI_DATABASE_zip | LOCAL_DB | LOCAL_MEDIA_DB | LOCAL_DB_PREV)
	ANKI_DATABASE_zip=files[1]
	done_a_download = False
	if os.path.exists(ANKI_DATABASE_zip):
		done_a_download = True

	# server is running an hour behind for some reason ? change this when it's fixed!
	if lastSeenOnline != "":
		# meaning failed to connect
		if lastSeenLocal < lastSeenOnline and done_a_download == False :
			response = askUser("You've been online recently, do you want to download any changes?")
			if response == False:
				tooltip("Rank Filter: %s" % str(RANK_FILTER_CHOICE))
				pass
			else:
				downloadFromMFC()
				tooltip("Downloding... Please dont cloze anki.", 5000)

		elif lastSeenLocal > lastSeenOnline:
			tooltip("Rank Filter: %s" % str(RANK_FILTER_CHOICE))
			# no changes done online, so leave it be
			pass

def setTokenToOnlineVer():
	url = address+'api/getSetRank'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		try:
			r = s.get(url, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
			if r.status_code != 200:
				if r.status_code == 401:
					pass
				else:
					showInfo("We had a problem connecting, maybe your token has expired?: Status Code %s" % r.status_code)
			else:
				response = json.loads(r.content)
				valu = response["user rank"]
				conn = sqlite3.connect(RANK_DATABASE)
				c = conn.cursor()
				c.execute("""update tokens set online_rank = ? where id = 1 """, (valu,))
				conn.commit()
				conn.close()
		except:
			# showInfo("Something went wrong when looking for your rank filter online.\nRestart Anki to refresh your rank filter if you want it changed.")
			pass


def pragmaCheck():
	url = address+'api/getPragma'
	tokenUsed = tokenizedAuth()
	if tokenUsed:
		s = requests.Session()
		r = s.get(url, auth=HTTPBasicAuth(tokenUsed[0],tokenUsed[1]))
		if r.status_code != 200:
			if r.status_code == 401:
				pass
			else:
				showInfo("We had a problem connecting, maybe your token has expired?: Status Code %s" % r.status_code)
		else:
			response = json.loads(r.content)
			resp = response["checkok"]
			if resp == "true":
				pass
			else:
				tooltip("A problem occured with your previous upload, so we are uploading again now!")
				uploadToMFC()

def getRankFromDb():
	setTokenToOnlineVer()
	conn = sqlite3.connect(RANK_DATABASE)
	c = conn.cursor()
	c.execute("""SELECT online_rank FROM tokens WHERE id = 1""")
	rank = c.fetchone()
	conn.close()
	if rank:
		rank = rank[0]
	else:
		rank = 0
	return rank

if MANUAL_RANK_FILTER_CHOICE:
	RANK_FILTER_CHOICE = MANUAL_RANK_FILTER_CHOICE
else:
	RANK_FILTER_CHOICE = getRankFromDb()

def runFlashCardAddon():
	global __window
	__window = FlashCardWindow()


def newloadedColStage():
	mw.progress.start(label="Running MFC addon checks with online DB", immediate=True)
	downloadZipCheck()
	pragmaCheck()
	mw.progress.update(label="pragmaCheck")
	setTokenToOnlineVer()
	mw.progress.update(label="Applying Filter to the cards")
	removeCardsOutOfRange()
	setLocalLast()
	newShow()
	mw.progress.finish()
	

addHook("profileLoaded",newloadedColStage)

connect = QAction("Medic Flashcards", mw)
connect.triggered.connect(runFlashCardAddon)
mw.form.menuTools.addAction(connect)



# AutoSync Addon for Anki
# Author: ftechz <github.com/ftechz/anki-autosync>
#
# Automatically synchronise the decks when idle for a certain period
# from aqt.utils import showInfo
# from aqt import mw
# from anki.hooks import addHook

class AutoSync:
	def syncDecks(self):
		"""Force sync if in any of the below states"""
		self.timer = None
		if mw.state in ["deckBrowser", "overview", "review"]:
			uploadToMFC()
		else:
			# Not able to sync. Wait another 2 minutes
			self.startSyncTimer(self.retryPeriod)

	def startSyncTimer(self, minutes):
		"""Start/reset the timer to sync deck"""
		if self.timer is not None:
			self.timer.stop()
		self.timer = mw.progress.timer(1000*60 * minutes, self.syncDecks, False)

	def resetTimer(self, minutes):
		"""Only reset timer if the timer exists"""
		if self.timer is not None:
			self.startSyncTimer(minutes)

	def stopTimer(self):
		if self.timer is not None:
			self.timer.stop()
		self.timer = None

	def updatedHook(self, *args):
		"""Start/restart timer to trigger if idle for a certain period"""
		self.startSyncTimer(self.idlePeriod)

	def activityHook(self, *args):
		"""Reset the timer if there is some kind of activity"""
		self.resetTimer(self.idlePeriod)

	def syncHook(self, state):
		"""Stop the timer if synced via other methods"""
		if state == "login":
			self.stopTimer()

	def __init__(self):
		self.idlePeriod = IDLE_PERIOD
		self.retryPeriod = RETRY_PERIOD
		self.timer = None

		updatedHooks = [
			"showQuestion",
			"reviewCleanup",
			"editFocusGained",
			"noteChanged",
			"reset",
			"tagsUpdated"
		]

		activtyHooks = [
			"showAnswer",
			"newDeck"
			]

		for hookName in updatedHooks:
			addHook(hookName, self.updatedHook)

		for hookName in activtyHooks:
			addHook(hookName, self.activityHook)

		addHook("sync", self.syncHook)

AutoSync()


