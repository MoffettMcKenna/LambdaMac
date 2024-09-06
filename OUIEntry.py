import os
import json
from enum import IntEnum


class BlockID(IntEnum):
    LARGE = 0
    MEDIUM = 1
    SMALL = 3
    UNKNOWN = 0xF


class OUIEntry:

    def __init__(self, line: str):
        lparts = line.split(',')
        i = 0

        # have to join things which were surrounded by "'s and held ,'s
        while i < len(lparts):
            if lparts[i].startswith('\"'):
                start = i
                while not lparts[i].strip().endswith('\"'):
                    i += 1
                end = i

                # set the starting index to all the pieces conbined
                lparts[start] = ','.join(lparts[start:end+1]).strip().strip('\"')
                # remove all the elements after start (start+1) through end (end+1)
                [lparts.remove(x) for x in lparts[start+1:end+1]]
                #end if startsw/
            else:
                i += 1
        #end while len(line)

        #now we have this arrangement:
        #   0 - block type
        #   1 - block
        #   2 - assignee
        #   3 - address
        match lparts[0].lower():
            case 'ma-m':
                self.block_type = BlockID.MEDIUM
            case 'ma-s':
                self.block_type = BlockID.SMALL
            case 'ma-l':
                self.block_type = BlockID.LARGE

        self._oui = lparts[1][:6]
        self._block = lparts[1][6:] # for large this will be empty
        self.assignee = lparts[2]
        self.address = lparts[3]


    @property
    def file(self):
        match self.block_type:
            case BlockID.SMALL:
                return f"small/{self._block[:2]}.json"
            case BlockID.MEDIUM:
                return f"med/{self.oui[:2]}.json"
            case BlockID.LARGE:
                return f"large/{self.oui[:4]}.json"

    @property
    def grant_type(self):
        match self.block_type:
            case BlockID.SMALL:
                return 'Small'
            case BlockID.MEDIUM:
                return 'Medium'
            case BlockID.LARGE:
                return 'Large'

    @property
    def oui(self):
        return self._oui

    @property
    def block(self):
        return self._block

    def _get_mask(self):
        match self.block_type:
            case BlockID.LARGE:
                return 'xxxxxx'
            case BlockID.MEDIUM:
                return 'xxxxx'
            case BlockID.SMALL:
                return 'xxx'
        # end match
    # end _get_mask

    def __str__(self):
        return f"{self.oui}:{self._block}{self._get_mask()}\t{self.name}"


class OUIParsingError(Exception):
    def __init__(self, msg, text):
        self.text = msg
        self._trigger = text

    def __str__(self):
        return f"{self.text}\n\t{self._trigger}"


