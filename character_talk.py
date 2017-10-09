#! /usr/bin/env python3


def get_sibling_directory_path(sibling_directory_name):
    '''
    returns path for a specified folder that is in the same parent directory as
        the current working directory
    '''

    import os

    current_path = os.getcwd()
    last_separator_position = current_path.rfind(os.sep)
    parent_directory_path = current_path[0:last_separator_position]
    sibling_directory_path = os.path.join(parent_directory_path,
                                          sibling_directory_name)
    return(sibling_directory_path)


def read_table(table_filepath, column_of_lists):
    '''
    reads table from 'csv' file
    each item in column 'column_of_lists' is read as a list; as currently
        written, the function can read only 1 column as a list
    '''

    import pandas as pd
    from ast import literal_eval

    # '^' used as separator because it does not appear in any text descriptions
    table = pd.read_csv(table_filepath, sep='^',
                        converters={column_of_lists: literal_eval})

    return(table)


def read_text_file(text_filename, as_string=False):
    '''
    reads each line in a text file as a list item and returns list by default
    if 'as_string' is 'True', reads entire text file as a single string
    '''

    text_list = []

    try:
        with open(text_filename) as text:
            if as_string:
                # reads text file as single string
                text_list = text.read().replace('\n', '')
            else:
                # reads each line of text file as item in a list
                for line in text:
                    text_list.append(line.rstrip('\n'))
            text.close()
        return(text_list)

    except:
        return('There was an error while trying to read the file')


def find_substring_idx(a_string, substring):
    '''
    returns starting and ending indices for a substring in 'a_string'
    if substring is empty (i.e., ''), returns lists of digits from zero to the
        length of 'a_string'
    '''

    import re

    start_idx = [s.start() for s in re.finditer(substring, a_string)]
    # don't need 'end_idx' for this project
    #end_idx = [e + len(substring) for e in start_idx]
    #return(start_idx, end_idx)

    return(start_idx)


def find_highest_token_below_max(tokens, max_position):
    '''
    '''

    max_token = []

    for i in range(len(tokens)):
        if tokens[i][1] < max_position:
            max_token = [tokens[i][0]]

    return(max_token)


def find_comic_quote_speakers(string_list, search_words):
    '''
    '''

    #import enchant
    from enchant.tokenize import get_tokenizer

    quotes_speaker = []
    last_string_speaker = ''
    tokenizer = get_tokenizer('en_US')
    no_quotes_counter = 0
    odd_quotes_counter = 0

    for i in range(len(string_list)):

        a_string = string_list[i]
        quotes_start_idx = find_substring_idx(a_string, '"')
        quotes_n = len(quotes_start_idx)
        tokens = [w for w in tokenizer(a_string) if w[0] in search_words]

        if quotes_n == 0:               # if there are no double quotes
            quotes_speaker.append([])   # can't identify any dialogue and must skip
            no_quotes_counter += 1

        elif (quotes_n % 2) != 0:       # if there is an odd number of double quotes
            quotes_speaker.append([])   # can't reliably identify dialogue and must skip
            odd_quotes_counter += 1

        else:
            panel = []
            for j in range(0, len(quotes_start_idx), 2):
                qs = find_highest_token_below_max(tokens, quotes_start_idx[j])
                if qs:
                    panel.append([qs[0], quotes_start_idx[j],
                                  quotes_start_idx[j+1]])
                    #quotes_speaker.append([qs[0], quotes_start_idx[j],
                    #                      quotes_start_idx[j+1]])
                else:
                    panel.append([last_string_speaker, quotes_start_idx[j],
                                  quotes_start_idx[j+1]])
                    #quotes_speaker.append([last_string_speaker,
                    #                       quotes_start_idx[j],
                    #                      quotes_start_idx[j+1]])
            quotes_speaker.append(panel)

        if tokens:
            last_string_speaker = tokens[-1][0]

    return(quotes_speaker, no_quotes_counter, odd_quotes_counter)


def find_comics_quote_speakers(table, table_col, search_words):
    '''
    '''

    message_interval = 100
    comics_list = []
    no_quotes_n = []
    odd_quotes_n = []
    table_len = len(table)

    for j in range(table_len):

        # loop status message
        if (j % message_interval) == 0:
            print('Processing file {0} of {1}, which is {2:.0f}%'
                .format(j + 1, table_len, 100 * (j + 1) / table_len))

        qs, nq, oq = find_comic_quote_speakers(table.iloc[j, table_col],
                                               search_words)

        comics_list.append(qs)
        no_quotes_n.append(nq)
        odd_quotes_n.append(oq)

    return(comics_list, no_quotes_n, odd_quotes_n)


def replace_patty(table):
    '''
    Replaces designations of 'patty' as the speaker with a designation for
        Peppermint Patty only on the dates where she appears in the strip
    This distinguishes Peppermint Patty from Patty (they never appear in the
        same comic strip)
    NOTE TO SELF:  it's more proper to correctly distinguish the speakers when
        the table is first created, instead of creating it and then correcting
        it, but in this case, it seemed more expedient to do it this way and
        also avoid cluttering the table-creation code with this ad hoc
        complication
    '''

    pep = 'pep_patty'       # abbreviated Peppermint Patty designation

    # dates of all of Peppermint Patty's appearances in Peanuts
    patty_dates = read_text_file('peppermint_patty_dates.txt')

    # NOTE TO SELF:  isn't there a more compact, efficient, vectorized way to
    #   iterate over arbitrary Pandas indices?
    patty_bool = table['filename'].isin(patty_dates)
    indices = list(patty_bool[patty_bool == True].index.values)

    for j in range(len(indices)):

        cell = table.iloc[indices[j], 7]

        for i in range(len(cell)):
            if not cell[i]:
                pass
            elif cell[i][0] == 'patty':
                cell[i][0] = pep

    return(table)


def main():
    '''
    Identifies speakers of dialogue in descriptions of comics
    Additionally, corrects descriptions to distinguish between Peanuts
        characters Patty and Peppermint Patty
    Reads table of descriptions from a 'csv' file and writes modified table
        with speaker information to new 'csv' file in current working directory
    Columns added to table are 'no_quotes_n', 'odd_quotes_n', and
        'comics_speakers'
    Speech (or thought balloons) are identified in the descriptions by
        enclosure in double quotes
    Descriptions with no double quotes present (i.e., no speech or thought) are
        counted; 'no_quotes_n' is added to modified table and contains the
        number of panels in a comic's description without double quotes
    In some cases, a description erroneously has an odd number of double quotes,
        which prevents demarcation of the speech and non-speech with certainty;
        in this case, the program marks the description by counting the number
        of panels in a comic's description with an odd number of double quotes
        (added in table under 'odd_quotes_n')
    Speaker of each instance of speech/thought in each panel is added to table
        under 'comics_speakers', which also includes positions of double quotes
        enclosing the speech/thought
    As noted below, current simple method for identifying speaker is not
        reliable enough for analysis; potential improvements are suggested below
    '''
    '''
    Notes after 1st run:  The very simple rule of choosing the most recently
        mentioned character as the speaker for a particular piece of dialogue
        did surprisingly well.  Out of a random sample of 50 comics, the rule
        correctly chose the speaker for 72.5% of dialogue 'pieces'/instances.
        That's still rather low, though, to trust results based on it.
    Potential simple improvements:
        1) Some pieces of dialogue occur at the start of the text description
            of the 1st panel of a comic, and the speaker is mentioned
            afterwards.  This causes the simple rule to assign no speaker to
            dialogue.  A simple fix would be to check after the speaker
            assignment step whether the speaker string is empty.  If so, one
            can check after the dialogue and assign the first mentioned
            character.
        2) The simple rule ignores pronouns.  Accounting for the pronouns
            and determining their referents could be complicated in the general
            case.  But in cases when there is only 1 girl and 1 boy and the
            comic, it would be easy to assign the pronoun to the correct
            speaker.
    Ongoing issues:
        For the 1st panel of the May 8, 1985 comic, the program doesn't assign
        the Literary Ace (or anyone) as the speaker, even though I added him to
        the character list before the 2nd run.  Is there a trailing space or
        typo preventing the match?
    '''

    import os

    table_folder = '05_spell_check'
    table_file = 'table.csv'
    table_filepath = os.path.join(get_sibling_directory_path(table_folder),
                                  table_file)

    table_col = 4
    text_col_name = 'text_spell_corrected'
    table = read_table(table_filepath, text_col_name)

    char_names_file = 'character_names.txt'
    search_words = read_text_file(char_names_file)
    search_words = [s.lower() for s in search_words]

    comics_speakers, no_quotes_n, odd_quotes_n = find_comics_quote_speakers(
        table, table_col, search_words)

    table['no_quotes_n'] = no_quotes_n
    table['odd_quotes_n'] = odd_quotes_n
    table['comics_speakers'] = comics_speakers

    table = replace_patty(table)

    table.to_csv('table.csv', sep='^', index=False)


if __name__ == '__main__':
    main()
