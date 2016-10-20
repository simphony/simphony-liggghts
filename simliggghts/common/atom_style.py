from enum import Enum


class AtomStyle(Enum):
    """ Supported atom styles

    """
    GRANULAR = 1

# mapping from liggghts style to AtomStyle
LIGGGHTS_STYLE = {'granular': AtomStyle.GRANULAR}


def get_atom_style(liggghts_atom_style):
    """ Return atom style from string

        Parameters
        ----------
        liggghts_atom_style : string
            string of liggghts style (i.e. from liggghts data file)

        Returns
        -------
        AtomStyle

        Raises
        ------
        RunTimeError
            If 'liggghts_style' is not recognized

    """
    try:
        return LIGGGHTS_STYLE[liggghts_atom_style]
    except KeyError:
        return RuntimeError(
            "Unsupported liggghts atom style: '{}'".format(
                                                liggghts_atom_style))


def get_liggghts_string(atom_style):
    """ Return atom style from string

        Parameters
        ----------
        atom_style : AtomStyle
            atom style

        Returns
        -------
        string
            liggghts string describing the atom style

        Raises
        ------
        RunTimeError

    """
    for liggghts_style, corresponding_atom_style in LIGGGHTS_STYLE.iteritems():
        if atom_style == corresponding_atom_style:
            return liggghts_style

    return RuntimeError(
        "Could not find liggghts atom style for '{}'".format(atom_style))
