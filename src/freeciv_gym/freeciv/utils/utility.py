# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


# def DIVIDE(n, d):
# * DIVIDE() divides and rounds down, rather than just divides and
# *rounds toward 0.  It is assumed that the divisor is positive."""
# return parseInt( (n) / (d) - (( (n) < 0 && (n) % (d) < 0 ) ? 1 : 0) )


def FC_WRAP(value, arange):
    # return (value % (arange) + (arange) if (value) % (arange) != 0 else 0) \
    return ((value + arange) % arange if value % arange != 0 else 0) \
        if value < 0 else (value % arange if value >= arange else value)


def XOR(a, b):
    return (a or b) and not (a and b)


def byte_to_bit_array(abyte_array):
    bit_array = []
    for abyte in abyte_array:
        bit_array.extend([int(x) for x in "{0:0>8}".format(bin(abyte)[2:])][::-1])
    return bit_array


def sign(x):
    return (x > 0) - (x < 0)
