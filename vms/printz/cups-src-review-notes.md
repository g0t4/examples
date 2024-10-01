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

    # injection risks from just truncating inputs?
      service_name[63] = '\0'

  # examine_discovered_printer_record
    https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L11763-L11770
      opens rwlock so this must IPP => PPD gen?

      https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L10210-L10766

        500+ LOC for this one new method

        assembles http uri => `uri` variable, later passed to cfGetPrinterAttributes
          https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L10448-L10450
            later is passed



  # create_remote_printer_entry
    https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L10518-L10523

    => cfGetPrinterAttributes (two+ spots)
      https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L7826-L7837
      https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L7897-L7898
      BOTH spots essentially only pass `uri` to cfGetPrinterAttributes

  # cfGetPrinterAttributes5 (ultimately called by cfGPA above)
    https://github.com/OpenPrinting/libcupsfilters/blob/before-patch/cupsfilters/ipp.c#L155-L165
      RESOLVES DNS-SD service name based URIs => hostname based URIs

    # httpConnect (to printer host)
      https://github.com/OpenPrinting/libcupsfilters/blob/before-patch/cupsfilters/ipp.c#L263-L265

      # cupsDoRequest
        https://github.com/OpenPrinting/libcupsfilters/blob/before-patch/cupsfilters/ipp.c#L313

      # interesting libcupsfilter => uses ippGetFirstAttribute (extern to cup), IIAC cups depends on libcupsfilters, is this a reverse dep then?

      # if successful attrs, but not media-col-database, try again:
        https://github.com/OpenPrinting/libcupsfilters/blob/before-patch/cupsfilters/ipp.c#L373-L406


# SEP

OK yup
  process_browse_data
    calls recheck_timer! ok there we go... right after `found_cups_printer` is done

  main/recheck_timer
    only callers to update_cups_queues
      SO IIGC after a short period of time the IPP=>PPD is requested using  this timer mechanism? perhaps for retry?

  update_cups_queues
    only caller to create_queue:
    create_queue
      https://github.com/OpenPrinting/cups-browsed/blob/before-patch/daemon/cups-browsed.c#L8125-L8126

      only caller to ppdCreatePPDFromIPP
        impl'd in ppd-generator.c
          https://github.com/OpenPrinting/libppd/blob/before-patch/ppd/ppd-generator.c#L182-L183


# ppdCreatePPDFromIPP
  *** yikez => this seems bad...I didn't take the time to review the actual impl but replacing the real impl seems like wow confusing for people reading the code to say the least  (SEEMS LIKE RIPE FOR EXPLOITS)
    `strlcpy` is macro'd to __ppd_strlcpy (this is a custom impl?), if so the semantics of this are HEADACHE... one might assume it's the library version... hopefully semantics match... do they?
      https://github.com/OpenPrinting/libppd/blob/before-patch/ppd/string-private.h#L167-L171
    same for several others:
      https://github.com/OpenPrinting/libppd/blob/before-patch/ppd/string-private.h#L152-L181
    IIAC cheritably, this is likely a way to port the strlcpy to platforms that don't have it? or historically that was reason

  # start of arg parsing with make/model
    https://github.com/OpenPrinting/libppd/blob/before-patch/ppd/ppd-generator.c#L333-L339

  # PATCHED IMPL notes
    https://github.com/OpenPrinting/libppd/blob/edf139324ae2a8023ff75545d4000c52f8090929/ppd/ppd-generator.c#L480C3-L493C28
      cupsLanguages is handled interestingly... traililng \" is appended after logic which means if something slipped in here and got past any validation it could inline once again additional IPP commands like  foomaticCommmandLine
        but currently it only allows "en" to be added... if so why the loop? and why add it multiople times?
          TODO look into more when I get time to look at post patches
    similar loop with new lines here:
      https://github.com/OpenPrinting/libppd/blob/edf139324ae2a8023ff75545d4000c52f8090929/ppd/ppd-generator.c#L591C1-L627C1 (two loops)

    no validation called on attr?
      https://github.com/OpenPrinting/libppd/blob/edf139324ae2a8023ff75545d4000c52f8090929/ppd/ppd-generator.c#L695C1-L725C4
        result goes into pdl_list, is htis used later then?

# BTW latest version of all repos use master repo on github:
https://github.com/OpenPrinting/libppd/blob/master/ppd/string-private.h#L152-L181
  I had a "before-patch" branch checked out in each of the four repos so those all won't work on github (change to master and adjust lines for changes if wanna see the stuff I highlighted above)
