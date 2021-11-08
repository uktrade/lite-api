class TestParty:
    def test_name_length_permissive(self, party_factory):
        """Ensure we allow longer names (we used to have a 100-char limit)"""
        assert party_factory(name="short name")
        assert party_factory(name="a" * 100)
        assert party_factory(name="a" * 1024)
