# cups-browsed src review

## cups-browsed.c

BROWSE_CUPS (symbol)
socket for 631/udp:
  https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L13982-L13983
process_browse_data
  https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L11795-L11799
  - on each packet sent to browsesocket

  allowed
    decide if server message allowed
      pretty much default config is allow all
    => why is this not in a firewall instead? why configure it in cups-browsed.conf files?!

  # process packet, x = unsigned hex int, thus two hex numbers plus a string up to 1023 chars,
  if (sscanf (packet, "%x%x%1023s", &type, &state, uri) < 3)
  {
    debug_printf("incorrect browse packet format\n");
    return (TRUE);
  }
    # `type` can be any hex value except CUPS_PRINTER_DELETE = 0x100000
    # `state` can be any hex value, beyond that it is ignored
    # IIAC evilsocket saw < 3 and assumed that meant "0 3" as in 3 in 2nd arg but sscanf is returning the number of successful matches, so < 3 means less than 3 successful matches, which means 2 or less successful matches
      # and this must be partially why uri is parsed and not used... and then reparsed into location/info... YET it is passed to next stage!

  # string must be "" delimited
  # why does this thing extract URI and then turn around and exract location too? that seems to overlap, why do it twice and have all this repeat logic for extracting location?
    # basically finds first " in packet and starts copying until next " or end of packet.. which is the same as `uri` extraction
    # then ensures there is " and only spaces after the 2nd quote
    # looking for an info field... ok but why parse uri at all with scanf?
    # btw looking for " again (3rd one) for start of implicit info field, then copies until either end of info size or end of packet or next " (4th one)
    #
