################################################################################
#   Project: legohdl
#   Script: graph.py
#   Author: Chase Ruskin
#   Description:
#       This script is a graph module mainly used to generate a flat dependency
#   tree from the DAG generated by legohdl. Performs topological sort.
################################################################################

import logging as log

class Graph:
    def __init__(self):
        #store with adj list (list of vertices)
        self.__adj_list = dict()
        self._unit_bank = dict()
        pass
    
    #takes in two entities and connects them [entity, dep-name]
    def addEdge(self, to, fromm): #to->upper-level module... from->lower-level module
        #add to list if vertex does not exist
        if(to not in self.__adj_list.keys()):
            self.__adj_list[to] = list()
        if(fromm not in self.__adj_list.keys()):
            self.__adj_list[fromm] = list()
        
        if(fromm not in self.__adj_list[to]):
            self.__adj_list[to].append(fromm)
            pass
        pass

    def addLeaf(self, to):
        self._unit_bank[to.getFull()] = to

    def removeEdge(self, to, fromm):
        if(fromm in self.__adj_list[to]):
            self.__adj_list[to].remove(fromm)
        pass

    def topologicalSort(self):
        order = [] # return list of design entities in their correct order

        block_order = [] # return list of blocks in their correct order
        block_tracker = [] # used for case-insensitive comparison

        def addBlock(m, l, n):
            nonlocal block_order, block_tracker

            mrkt_prepend = ''
            if(m != None):
                mrkt_prepend = m+'.'
            #check if block has already been added
            title = mrkt_prepend+l+'.'+n
            if(title.lower() in block_tracker):
                return
            block_tracker.append(title.lower())
            block_order.append(title)

        nghbr_count = dict()
        #print(len(self.__adj_list))
        #determine number of dependencies a vertex has
        for v in self.__adj_list.keys():
            nghbr_count[v] = len(self.__adj_list[v])
        #no connections were made, just add all units found
        if(len(self.__adj_list) == 0):
            log.warning("No edges found.")
            for u in self._unit_bank.values():
                order.append(u)
                addBlock(u.getMarket(), u.getLib(low=False), u.getBlock(low=False))
  
        #continue until all are transferred
        while len(order) < len(self.__adj_list):
            #if a vertex has zero dependencies, add it to the list
            for v in nghbr_count.keys():
                if nghbr_count[v] == 0:
                    unit = self._unit_bank[v]
                    if(not unit.isPKG() or True):
                        #print(unit)
                        #add actual unit object to list
                        order.append(unit) 
                    #add block name to list
                    addBlock(unit.getMarket(), unit.getLib(low=False), unit.getBlock(low=False))
                    #will not be recounted
                    nghbr_count[v] = -1 
                    #who all depends on this module?
                    for k in self.__adj_list.keys():
                        if(v in self.__adj_list[k]):
                            #decrement every vertex dep count that depended on recently added vertex
                            nghbr_count[k] = nghbr_count[k] - 1
                    continue

        if(len(block_order) == 0):
            exit(log.error("Invalid current block, try adding a VHDL file"))
        return order,block_order

    #only display entities in the tree (no package units)
    def output(self, top, leaf='+-'):
        first = (leaf == '+-')
        #print title if method is on top-level entity
        if(first):
            print('---DEPENDENCY TREE---')
        #start with top level
        if(top not in self._unit_bank.keys()):
            exit(log.error('Entity '+top+' may be missing an architecture.'))
        if(not self._unit_bank[top].isPKG()):
            #uncomment this next line to print market along with entity
            #print(leaf,self._unit_bank[top].getMarket()+'.'+top)
            temp_leaf = leaf
            #skip first bar because everything is under top-level entity
            if(not first):
                temp_leaf = ' '+leaf[1:]
            #print to console
            print(temp_leaf,top)
        if(len(self.__adj_list) == 0):
            return
        for sub_entity in self.__adj_list[top]:
            next_leaf = '| '+leaf
            #remove rightmost bar if the parent is the end of a branch
            if(leaf.count('\\')):
                last_bar = next_leaf.rfind('|')
                next_leaf = next_leaf[:last_bar] + ' ' + next_leaf[last_bar+1:]
            #add trailing slant if end of the branch
            if(sub_entity == self.__adj_list[top][-1]):
                next_leaf = next_leaf.replace('+','\\')

            self.output(sub_entity, next_leaf)
        pass

    def getVertices(self):
        return len(self.__adj_list)

    pass