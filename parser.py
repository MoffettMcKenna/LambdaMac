import os
import json
from enum import IntEnum


class BlockID(IntEnum):
    LARGE = 0
    MEDIUM = 1
    SMALL = 3
    UNKNOWN = 0xF


class OUIEntry:

    def __init__(self, oui, name):
        self.oui = oui
        self.name = name.strip()
        self.block_type = BlockID.LARGE
        self._block = ''

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
    def block(self):
        return self._block

    @block.setter
    def block(self, t: tuple):
        a = t[0]
        b = t[1]
        if b[1:].lower() == 'fffff' and a[1:] == '00000':
            self.block_type = BlockID.MEDIUM
            self._block = b[0]
        elif b[3:].lower() == 'fff' and a[3:] == '000':
            self.block_type = BlockID.SMALL
            self._block = b[:3]
        else:
            raise OUIParsingError("Unable to identify block type", '') 

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


def read_oui_line(infile):
    ln = infile.readline()

    # not expected, but a safety value
    while ln == '\n':
        ln = infile.readline()

    # expect two pieces with tabs in the middle, first part is oui with markers, second is org name
    # any junk in the middle will be ignored
    parts = ln.split('\t')
    if len(parts) < 2:
        raise OUIParsingError("Invalid line, did not split into two pieces.", ln)

    # break-up line on spaces and convert oui from AA-BB-CC to AABBCC
    oui = parts[0].split()[0].replace("-", "")

    entry = OUIEntry(oui, parts[-1])
    return read_range(f, entry)


def read_range(infile, entry):
    ln = infile.readline().strip()

    parts = ln.split()[0].split('-')

    if len(parts) > 1:
        try:
            entry.block = (parts[0], parts[1])
        except OUIParsingError as e:
            raise OUIParsingError(e.text, ln)
    # end if len(parts)
    # no need to do anything for MA-L case, that's the default

    return entry
# end read_range()


def peek(oui_file):
    spot = oui_file.tell()
    ln = oui_file.readline()
    oui_file.seek(spot)
    return ln


def pad_oui(entry):
    match entry.block_type:
        case BlockID.LARGE:
            return ''
        case BlockID.MEDIUM:
            return '     '
        case BlockID.SMALL:
            return '   '


base = 'ouis'

for file in os.listdir(base):
    # this needs to be pulling from ieee site if the local copy is different size from ieee version
    print(f"running file {file}")

    with open(f"{base}/{file}", encoding='UTF-8') as f:
        line = f.readline()

        # loop past the header
        while line != '\n':
            line = f.readline()

        x = 0

        # stop if this line or the next is EOF
        while line and peek(f):

            # skip any extra lines
            if peek(f) == '\n':
                continue

            try:
                oe = read_oui_line(f)
                # print(f"{oe.oui}:{oe.block}{pad_oui(oe)}\t{oe.file}\t{oe.name}")
            except OUIParsingError as pe:
                print(f"skipping entry, {str(pe)}")

            # make sure we have a folder to write inside
            if not os.path.exists(os.path.dirname(oe.file)):
                os.makedirs(os.path.dirname(oe.file))

            data = {}
            write = False

            # reasons this works:
            #   * the data partitioning is being optimized for small file sizes
            #       -> fast transfer, load, and write
            #   * so we're never bloating memory by opening a large file or slowing down for lots of IOS
            if os.path.exists(oe.file):
                with open(oe.file, 'r', encoding='UTF-8') as jfile:
                    data = json.load(jfile)

                # oui is in the file
                if oe.oui in data.keys():
                    # special handling for large block assignments
                    if oe.block_type == BlockID.LARGE:
                        if data[oe.oui] != oe.name:
                            data[oe.oui] = oe.name
                            write = True
                        # else no change needed
                    # end if block_type large
                    else:
                        # do we have the block represented?
                        if oe.block in data[oe.oui].keys():
                            # if the name is the same stop processing
                            if data[oe.oui][oe.block] != oe.name:
                                data[oe.oui][oe.block] = oe.name
                                write = True
                        # don't have this block for the oui, just add it
                        else:
                            data[oe.oui][oe.block] = oe.name
                            write = True
                    # end else (block type = med/small)
                # just add the oui with this entry as the only one
                else:
                    data[oe.oui] = oe.name if oe.block_type == BlockID.LARGE else {oe.block: oe.name}
                    write = True

                # save any updates
                if write:
                    with open(oe.file, 'w', encoding='UTF-8') as jfile:
                        jfile.write(json.dumps(data))
                # end if write
            # end if file exists

            # create file with initial data
            else:
                # a long line is better than 5
                data[oe.oui] = oe.name if oe.block_type == BlockID.LARGE else {oe.block: oe.name}
                with open(oe.file, 'x', encoding='UTF-8') as jfile:
                    jfile.write(json.dumps(data))
                # end with create file
            # end else

            # search for the empty line between entries, skipping the contact details
            line = f.readline()
            while line != '\n' and line:
                line = f.readline()
            x += 1
        # end while line and peek()
    # end with open()
    print(f"file {file} complete\n")
# end for file
