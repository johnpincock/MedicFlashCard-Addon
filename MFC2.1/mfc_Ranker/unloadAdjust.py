# import the main window object (mw) from aqt
from aqt.utils import showInfo, showWarning
from aqt import mw

# import the "show info" tool from utils.py

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
def newunloadCollection(onsuccess):
	def callback():
		mw.setEnabled(False)
		uunloadCollection()
		if onsuccess:
			onsuccess()
	mw.closeAllWindows(callback)
	mw.app.exit(0)

def uunloadCollection():
	# BB = mw.col.db.scalar("pragma integrity_check")
	# showInfo(BB)
	# mw.col.close()
	if not mw.col:
		return
	if mw.restoringBackup:
		label = _("Closing...")
	else:
		label = _("Backing Up...")
	mw.progress.start(label=label, immediate=True)
	corrupt = False
	closeError = False
	try:
		mw.maybeOptimize()
		corrupt = mw.col.db.scalar("pragma integrity_check") != "ok" 
	except Exception as e: 
		corrupt=True
		showInfo("%s"%e)
	try:
		mw.col.close()
	except Exception as e: 
		# showInfo("%s"%e)
		if "attempt to write a readonly database" in str(e):
			closeError = False
		else:
			closeError = True
	finally:
		mw.col = None
	if corrupt:
		showWarning(_("Your collection file appears to be corrupt. \
This can happen when the file is copied or moved while Anki is open, or \
when the collection is stored on a network or cloud drive. If problems \
persist after restarting your computer, please open an automatic backup \
from the profile screen."))
	if closeError:
		showInfo(_("Problem encountered when closing the the database."))
	if not corrupt and not mw.restoringBackup:
		mw.backup()
	mw.progress.finish()
	

# unloadcol = mw._unloadCollection
mw.unloadCollection = newunloadCollection
