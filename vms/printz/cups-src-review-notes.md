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
    # `type` can be any hex value except NOT bit at: CUPS_PRINTER_DELETE = 0x100000 (!(type & CUPS_PRINTER_DELETE)) # bitwise check
    # `state` can be any hex value, beyond that it is ignored
    # IIAC evilsocket saw < 3 and assumed that meant "0 3" as in 3 in 2nd arg but sscanf is returning the number of successful matches, so < 3 means less than 3 successful matches, which means 2 or less successful matches
      # and this must be partially why uri is parsed and not used... and then reparsed into location/info... YET it is passed to next stage!

  # ok I misunderstood earlier... `sscanf` advances the pointer past the first three fields extracted...
    so overall format, IIUC:
      `type state uri "location" "info"`
      confirmed this works:
        `callback_url = f"FF 10 {attacker_http_printer} \"your_mom\" \"fooinfo\""`
      => info alters the name of the printer
        "fooinfo" => "fooinfo_192_168_122_1" (for example)


  # calls found_cups_printer(remote_host, uri, location, info)
    # remote_host from socket addr
    #   via `httpAddrString(&srcaddr [from socket], remote_host...)
    # location (sscanf) / location/info from for loop

# found_cups_printer
  # httpSeparateURI
    # acccepts many diff schemes it seems, or at least parses them out
      https://github.com/openprinting/cups/blob/before-patch/cups/http-support.c#L946-L959

  # resource must contain /printers or /classes
    https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L11734-L11741

  # build equiv DNS-SD service name (CUPS => DNS-SD)
    https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L11747-L11763
