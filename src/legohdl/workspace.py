# Project: legohdl
# Script: workspace.py
# Author: Chase Ruskin
# Description:
#   The Workspace class. A Workspace object has a path and a list of available
#   markets. This is what the user keeps their work's scope within for a given
#   "organization".

import os
from .apparatus import Apparatus as apt
from .map import Map
import logging as log
from .market import Market
import shutil

class Workspace:

    #store all workspaces in dictionary
    Jar = Map()

    #active-workspace is a workspace object
    _ActiveWorkspace = None


    def __init__(self, name, path, markets=[]):
        '''
        Create a workspace instance.

        Parameters:
            name (str): the identity for the workspace
            path (str): the local path where blocks will be looked for
            markets ([str]): the list of markets that are tied to this workspace
        Returns:
            None
        '''
        self._name = name
        #do not create workspace if the name is already taken
        if(self.getName().lower() in self.Jar.keys()):
            log.error("Skipping workspace "+self.getName()+" due to duplicate naming conflict.")
            return

        #set the path
        self._path = ''
        self.setPath(path)
        #do not create workspace if the path is empty
        if(self.getPath() == ''):
            log.error("Skipping workspace "+self.getName()+" due to empty local path.")
            return
        
        self._ws_dir = apt.fs(apt.HIDDEN+"workspaces/"+self.getName()+"/")
        
        #ensure all workspace hidden directories exist
        if(os.path.isdir(self.getWorkspaceDir()) == False):
            log.info("Creating hidden workspace directory for "+self.getName()+"...")
            os.makedirs(self.getWorkspaceDir(), exist_ok=True)
        #store the code's state of each version for each block
        os.makedirs(self.getWorkspaceDir()+"cache", exist_ok=True)
        #create the refresh log
        if(os.path.isfile(self.getWorkspaceDir()+apt.REFRESH_LOG) == False):
            open(self.getWorkspaceDir()+apt.REFRESH_LOG, 'w').close()

        self._markets = []
        #find all market objects by name and store in list
        for mrkt in markets:
            if(mrkt.lower() in Market.Jar.keys()):
                self._markets += [Market.Jar[mrkt]]
            else:
                log.warning("Could not link unknown market "+mrkt+" to "+self.getName()+".")
            pass

        #add to class Jar
        self.Jar[self.getName()] = self
        pass


    def setPath(self, p):
        '''
        Set the workspace's local path to a new value. Will ask user if okay
        to create the path if DNE.

        Parameters:
            p (str): the path string
        Returns:
            (bool): true if successfully changed the path attribute
        '''
        #cannot set an empty path
        if(p == '' or p == None):
            log.info("Workspace "+self.getName()+"'s local path cannot be empty.")
            return False

        p = apt.fs(p)
        #create the workspace's local path if it does not exist
        if(os.path.exists(p) == False):
            #prompt user
            carry_on = apt.confirmation("Workspace "+self.getName()+"'s local path does not exist. Create "+p+"?")
            if(carry_on):
                os.mkdir(p)
                self._path = p
                return True
            else:
                log.info("Did not set "+p+" as local path.")
                return False
        else:
            self._path = p
            return True


    def setName(self, n):
        '''
        Change the workspace's name if the name is not already taken.

        Parameters:
            n (str): new name for workspace
        Returns:
            (bool): true if name successfully altered and updated in Jar
        '''
        if(n == '' or n == None):
            log.error("Workspace name cannot be empty.")
            return False

        if(n.lower() in self.Jar.keys()):
            log.error("Cannot rename workspace to "+n+" due to name conflict.")
            return False
        else:
            #remove old name from Jar
            if(self.getName().lower() in self.Jar.keys()):
                del self.Jar[self.getName()]

            #rename hidden directory if exists
            new_dir = apt.fs(apt.HIDDEN+"workspaces/"+n+"/")
            if(hasattr(self, "_ws_dir")):
                os.rename(self.getWorkspaceDir(), new_dir)
            #set the hidden workspace directory
            self._ws_dir = new_dir

            #change to new name
            self._name = n
            #update the Jar
            self.Jar[self.getName()] = self
            return True

    def remove(self):
        '''
        Removes the workspace object from the Jar and its hidden directory.

        Parameters:
            None
        Returns:
            None
        '''
        log.info("Removing workspace "+self.getName()+"...")
        #delete the hidden workspace directory
        shutil.rmtree(self.getWorkspaceDir(), onerror=apt.rmReadOnly)
        #remove from class Jar
        del self.Jar[self.getName()]
        pass


    def linkMarket(self, mrkt):
        '''
        Attempts to add a market to the workspace's market list.

        Parameters:
            mrkt (str): name of the market to add
        Returns:
            (bool): true if the market list was modified (successful add)
        '''
        if(mrkt.lower() in Market.Jar.keys()):
            mrkt_obj = Market.Jar[mrkt]
            if(mrkt_obj in self.getMarkets()):
                log.info("Market "+mrkt_obj.getName(low=False)+" is already linked to this workspace.")
                return False
            else:
                log.info("Linking market "+mrkt_obj.getName(low=False)+" to the workspace...")
                self._markets += [mrkt_obj]
                return True
        else:
            log.warning("Could not link unknown market "+mrkt+" to "+self.getName()+".")
            return False


    def unlinkMarket(self, mrkt):
        '''
        Attempts to remove a market from the workspace's market list.

        Parameters:
            mrkt (str): name of the market to remove
        Returns:
            (bool): true if the market list was modified (successful remove)
        '''
        if(mrkt.lower() in Market.Jar.keys()):
            mrkt_obj = Market.Jar[mrkt]
            if(mrkt_obj not in self.getMarkets()):
                log.info("Market "+mrkt_obj.getName(low=False)+" is already unlinked from the workspace.")
                return False
            else:
                log.info("Unlinking market "+mrkt_obj.getName(low=False)+" from the workspace...")
                self._markets.remove(mrkt_obj)
                return True
        else:
            log.warning("Could not unlink unknown market "+mrkt+" from "+self.getName()+".")
            return False


    @classmethod
    def setActiveWorkspace(cls, ws):
        '''
        Set the active workspace after initializing all workspaces into Jar. If
        the input name is invalid, it will set the first workspace in the Jar as
        active.

        Parameters:
            ws (str): workspace name
        Returns:
            (bool): true if active-workspace was set
        '''
        if(ws != None and ws.lower() in cls.Jar.keys()):
            re_assign = (cls._ActiveWorkspace != None)
            #set the active workspace obj from found workspace
            cls._ActiveWorkspace = cls.Jar[ws]
            #only give prompt if reassigning the active-workspace
            if(re_assign):
                log.info("Assigning workspace "+cls._ActiveWorkspace.getName()+" as active workspace...")

            return True
        elif(len(cls.Jar.keys()) and cls._ActiveWorkspace == None):
            random_ws = list(cls.Jar.keys())[0]
            cls._ActiveWorkspace = cls.Jar[random_ws]
            log.info("Workspace "+ws+" does not exist. Auto-assigning active workspace to "+cls._ActiveWorkspace.getName()+"...")
            return True
        else:
            log.info("Workspace "+ws+" does not exist. Keeping "+cls._ActiveWorkspace.getName()+" as active.")
        return False


    def getPath(self):
        return self._path


    def getWorkspaceDir(self):
        return self._ws_dir


    def getName(self):
        return self._name


    def getMarkets(self):
        return self._markets


    def isActive(self):
        return self == self.getActiveWorkspace()


    @classmethod
    def getActiveWorkspace(cls):
        return cls._ActiveWorkspace


    def __str__(self):
        return f'''
        ID: {hex(id(self))}
        Name: {self.getName()}
        Path: {self.getPath()}
        Active: {self.isActive()}
        Hidden directory: {self.getWorkspaceDir()}
        Markets: {self.getMarkets()}
        '''

    pass