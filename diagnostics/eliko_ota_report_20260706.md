Hi all, hope you had a good weekend. I've been trying to recreate the "dead"/disconnected wand and have caught an issue in the logs using the single-anchor setup. Maybe this is related to the dropouts we're seeing (or it could be unrelated and I'm doing something wrong whilst using a single anchor).

I'm using one anchor (id 0x1D99) on USB-serial to a macOS host, tag 0x1DAD streaming IMU (PR) data. Tag boot banner reports VERS 0x05000000.

As of midday today the tag is stuck in a reboot loop: it boots, streams PR fine, then dies at almost exactly 10.2 seconds of uptime (occasionally ~30s or ~60s instead). Nothing changed on our side when it started - the tag hadn't moved, and our host hadn't sent a single byte for over an hour before the first reboot (its first send of the loop is the CMD0 re-enable in response to the boot banner).

At the same time, the anchor has started printing this on pretty much every ranging round (~every 100–200ms, non-stop):

    $PEKIO,AC,123,0x1DAD,CMD0,value,0x19000903,OTA

Is it that a stored CMD0 is stuck in one of the anchor's OTA slots and being re-delivered forever, and the endless delivery is what's knocking the tag over?

On startup (and whenever we see a tag boot banner) we send one IMU-enable per tag plus a subscribe:

    $PEKIO,DC,<seq>,CMD0,0x1DAD,0x00000903     (preamble code 9, PR data type)
    $PEKIO,DC,<seq>,SPQF,P

Each CMD0 gets acked as stored:

    $PEKIO,AC,<seq>,0,STORED,num_free_OTA_slots=159

One thing I spotted: num_free_OTA_slots has said 159 in every ack we have on record, going back weeks. So it looks like one slot has been permanently occupied for a long time.

Here's one full reboot cycle from a raw serial capture today (6 July, ~13:06 local). The tag's last PR is at tag-clock ~0x27BF, then the 5× PP,VERS boot banner, then PR restarts from sequence 001 with the clock rewound. Our host fires its CMD0 re-enable when it sees the banner (that's the DC,041), and the AC,123 delivery notice shows up a few ms later:

    13:06:03.966334 $PEKIO,PR,116,0x1D99,0x1DAD,003,0x000027BF,...
    13:06:04.082765 $PEKIO,PP,000,0x1DAD,VERS,0x05000000
    13:06:04.084108 $PEKIO,DC,041,CMD0,0x1DAD,0x00000903
    13:06:04.084201 $PEKIO,AC,041,0,STORED,num_free_OTA_slots=159
    13:06:04.085468 $PEKIO,PP,001,0x1DAD,VERS,0x05000000
    13:06:04.088284 $PEKIO,PP,002,0x1DAD,VERS,0x05000000
    13:06:04.091087 $PEKIO,PP,003,0x1DAD,VERS,0x05000000
    13:06:04.093943 $PEKIO,PP,004,0x1DAD,VERS,0x05000000
    13:06:04.096589 $PEKIO,AC,123,0x1DAD,CMD0,value,0x19000903,OTA
    13:06:04.171750 $PEKIO,PR,001,0x1D99,0x1DAD,003,0x00000073,...

The exact same pattern repeats 10.047s later, and again 10.047s after that — and the tag clock at the moment of death (0x27BF) is identical each time. That regularity is what makes us think watchdog/stall rather than a power event; the potential battery brown-out/battery disconnection reboots we've seen in the past are randomly timed.

Between reboots, the AC,123 ... OTA line just keeps coming:

    13:06:02.256765 $PEKIO,AC,123,0x1DAD,CMD0,value,0x19000903,OTA
    13:06:02.375808 $PEKIO,AC,123,0x1DAD,CMD0,value,0x19000903,OTA

I only ever send CMD0 with value 0x00000903, but the delivery notice reports 0x19000903 — there's a 0x19 (25) in the high byte that I didn't put there. Back in June we saw the same style of line for our other tag with a different high byte:

    2026-06-02  $PEKIO,AC,123,0x1DAE,CMD0,value,0xFA000903,OTA    (0xFA = 250)

And the 123 is the same across both tags and across weeks, so I don't think it's my command sequence number. (Is 123 a fixed notification id, and the high byte something the anchor attaches - retry counter, TTL, something like that maybe?)

- 2–3 June — occasional AC,123 lines for tag 0x1DAE, value 0xFA000903. A few per day.
- 3 July — same for tag 0x1DAD, value 0x19000903, about every 23 minutes. num_free_OTA_slots already 159. Everything otherwise normal (3 reboots all day, randomly timed).
- 6 July, 12:50 local — reboot loop starts spontaneously: host idle for 77 minutes beforehand (no commands sent), tag stationary, same anchor. First reboots come at growing intervals (15s, 28s, 42s, 66s, 94s), then settle to ~24s and finally a steady 10s. AC,123 goes from every ~23 minutes to every ranging round.

Is there a way to list or flush the stored OTA slots (or does power-cycling the anchor clear them)? Happy to send over the raw captures and full logs if useful.
