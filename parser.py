import os
import json
from OUIEntry import BlockID, OUIEntry, OUIParsingError
import logging

def pad_oui(entry):
    match entry.block_type:
        case BlockID.LARGE:
            return ''
        case BlockID.MEDIUM:
            return '     '
        case BlockID.SMALL:
            return '   '


def get_files() -> list[str]:
    for x in os.listdir():
        if x.endswith('.csv'):
            yield x
    # TODO factory approach for local vs aws
    # TODO make sure files are up to date first

def parsefile(file: str):
    exists = True
    logging.info(f"Parsing File {file}")
    
    with open(file) as f:
        headers = f.readline()
        for line in f:
            oe = OUIEntry(line)

            # make sure we have a folder to write inside
            if not os.path.exists(os.path.dirname(oe.file)):
                exists = False
                os.makedirs(os.path.dirname(oe.file))

            data = {}
            write = False

            # reasons this works:
            #   * the data partitioning is being optimized for small file sizes
            #       -> fast transfer, load, and write
            #   * so we're never bloating memory by opening a large file or slowing down for lots of IOS
            if os.path.exists(oe.file):
                logging.info(f"File {oe.file} exists") if not exists else None 
                with open(oe.file, 'r', encoding='UTF-8') as jfile:
                    data = json.load(jfile)

                # oui is in the file
                if oe.oui in data.keys():
                    # special handling for large block assignments
                    if oe.block_type == BlockID.LARGE:
                        if data[oe.oui] != oe.assignee:
                            data[oe.oui] = oe.assignee
                            write = True
                        # else no change needed
                    # end if block_type large
                    else:
                        # do we have the block represented?
                        if oe.block in data[oe.oui].keys():
                            # if the name is the same stop processing
                            if data[oe.oui][oe.block] != oe.assignee:
                                data[oe.oui][oe.block] = oe.assignee
                                write = True
                        # don't have this block for the oui, just add it
                        else:
                            data[oe.oui][oe.block] = oe.assignee
                            write = True
                    # end else (block type = med/small)
                # just add the oui with this entry as the only one
                else:
                    logging.info(f"Adding oui {oe.oui} to {oe.file}")
                    data[oe.oui] = oe.assignee if oe.block_type == BlockID.LARGE else {oe.block: oe.assignee}
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
                data[oe.oui] = oe.assignee if oe.block_type == BlockID.LARGE else {oe.block: oe.assignee}
                with open(oe.file, 'x', encoding='UTF-8') as jfile:
                    jfile.write(json.dumps(data))
                # end with create file
            # end else

        #end for line
    #with open()
#end parsefile()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    for file in get_files():
        parsefile(file)
    #end for file
    
    exit()

# end main
