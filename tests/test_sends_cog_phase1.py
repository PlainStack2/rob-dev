from rob.discord.cogs import sends as sends_cog


def test_legacy_manual_send_methods_are_supported():
    assert sends_cog._MANUAL_METHODS == ["cashapp", "venmo", "paypal", "onlyfans", "loyalfans", "youpay", "other"]


def test_sendrequest_methods_match_manual_methods():
    assert sends_cog._REQUEST_METHODS == sends_cog._MANUAL_METHODS

