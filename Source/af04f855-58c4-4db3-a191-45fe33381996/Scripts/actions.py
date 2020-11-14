# -- coding: utf-8 --
import re
from datetime import datetime
import time

######################
####### EVENTS #######
######################

def OverrideCardsMoved(args):
	cards = args.cards
	toGroup = args.toGroups
	xCard = args.xs
	yCard = args.ys
	i = 0
	for card in cards:
		if toGroup[i] == table:
			x = xCard[i]
			y = yCard[i]
			if card.group == me.hand:
				# whisper("moving from hand to table")
				card.moveToTable(x,y,True)
				flipAllCardsIfNeeded()
			if card.group == table:
				# whisper("moving from table to table")
				if shouldGrid(x):
					card.moveToTable(xGrid(x),yGrid(y))
				else:
					card.moveToTable(x,y)
					card.select()
		else:
			whisper("moving elsewhere")
			card.moveTo(toGroup[i])
		i += 1

def OnCardDoubleClicked(args):
	cardsToGet = [card for card in table if card.position[0] < 20 and card.position[1] == args.card.position[1]]
	multiplicate(cardsToGet)

######################
####### SETUP  #######
######################	

def setup(args=[], first=True):
	if iAmHost():
		mute()
		
		if first:
			notify("################################")
			notify("Pour jouer :\n")
			notify("- Tous les joueurs jouent une carte dans la zone de préparation")
			notify("- Les classer")
			notify("- Double-cliquer une carte pour récupérer toute la ligne")
			notify("- Lorsque plus personne n'a de cartes, lancer un nouveau Round en faisant un clic droit sur la table\n")
			notify("Le premier joueur qui a 66 vachettes déclenche la fin de partie.")
			notify("Le joueur qui a le moins de vachettes l'emporte.")
			notify("################################")
		else:
			notify("La nouvelle partie commence !")
			for card in shared.pioche:
				card.delete()
			if gameIsOver():
				return True
			
		setGlobalVariable("dateTimeDebut", time.mktime(datetime.now().timetuple()))
		createRangeCards(shared.pioche, 1, 104)
		shared.pioche.shuffle()
		
		#on met les cartes de bases
		baseCards = [card for card in shared.pioche.top(4)]
		baseCards.sort(key=lambda x:int(x.Name))
		y = -410
		for card in baseCards:
			card.moveToTable(-650, y)
			y += 210
		
		personnalSetup()

def personnalSetup():
	mute()
	shared.pioche.shuffle()
	myCards = [card for card in shared.pioche.top(10)]
	myCards.sort(key=lambda x:int(x.Name))
	for card in myCards:
		card.moveTo(me.hand)
	
	if me._id < len(getPlayers()):
		remoteCall(getNextPlayer(), "personnalSetup", [])

######################
####### UTILS  #######
######################

def iAmHost():
	return me._id == 1

def remoteCallAll(functionName, params = []):
	mute()
	for p in getPlayers():
		if p._id != me._id: #no network call for me
			remoteCall(p,functionName,params)
	globals()[functionName](*params) #local call for me

def notifyBarAll(message, color = "#FF0000"):
	message = " "*250 + message + " "*250
	remoteCallAll("notifyBar",[color,message])
	notify(message)

def createRangeCards(destination, fromID, toID):
	for i in range(fromID, toID+1):
		destination.create("00000001-0000-0096-0001-000000000{}".format(str(i).zfill(3)))

def printGameDuration(a=0,b=0,c=0):
	begin = datetime.fromtimestamp(eval(getGlobalVariable("dateTimeDebut")))
	duration = datetime.utcfromtimestamp((datetime.now() - begin).total_seconds())
	notify("La partie a durée {}".format(duration.strftime('%Hh%Mmin%Ss')))

def getNextPlayer():
	return Player((me._id % len(getPlayers()))+1)

def flipAllCardsIfNeeded():
	# whisper("flipAllCardsIfNeeded {}".format(me))
	downCounter = 0
	for card in table:
		if card.isFaceUp == False:
			downCounter += 1
	# whisper("downCounter:{}".format(downCounter))
	if downCounter >= len(getPlayers()):
		# whisper("flipping")
		for card in table:
			card.isFaceUp = True

def xGrid(x):
	result = ((x+20)//140)*140+50
	# whisper("rounding x from {} into {}".format(x, result))
	return result

def yGrid(y):
	result = ((y+105)//210)*210+10
	# whisper("rounding y from {} into {}".format(y, result))
	return result

def shouldGrid(x):
	return x < 20

def multiplicate(cards):
	mute()
	total = len(cards)
	for card in cards:
		quantity = 0
		if eval(card.Name) == 55:
			quantity += 6
		elif eval(card.Name) % 11 == 0:
			quantity += 4
		elif eval(card.Name) % 10 == 0:
			quantity += 2
		elif eval(card.Name) % 5 == 0:
			quantity += 1
		me.Points.create(card.model, quantity)
		card.moveTo(me.Points)
		total += quantity
	
	notify("{} prends {} vachette{}".format(me, total, pluriel(total)))

def pluriel(quantity):
	pluriel = ""
	if quantity > 1:
		pluriel = "s"
	return pluriel

def gameIsOver():
	sortedPlayers = [player for player in getPlayers()]
	sortedPlayers.sort(key=lambda x:len(x.Points))
	
	gameOver = False
	for player in sortedPlayers:
		if len(player.Points) >= 66:
			gameOver = True
	
	if gameOver:
		points = len(sortedPlayers[0].Points)
		notifyBarAll("La partie est terminée, {} l'emporte avec {} vachette{}".format(sortedPlayers[0], points, pluriel(points)))
		printGameDuration()
	
	return gameOver

def cleanMyBoard(a=0):
	mute()
	for card in table:
		if card.controller._id == me._id:
			card.delete()

##############################
####### TABLE ACTIONS  #######
##############################

def canNewRound(a=0,b=0,c=0):
	return iAmHost() and len(me.hand) == 0

def newRound(a=0,b=0,c=0):
	mute()
	remoteCallAll("cleanMyBoard")
	setup(first=False)