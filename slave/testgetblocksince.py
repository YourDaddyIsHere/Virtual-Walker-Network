from HalfBlockDatabase import HalfBlockDatabase,HalfBlock

database = HalfBlockDatabase()
database2 = HalfBlockDatabase(database_name="BlockDataBaseactive.db")
#blocks = database.get_all_blocks()
member = database2.get_all_member()
#print blocks[510].up
blocks_since = database.get_blocks_since(public_key = member[1],sequence_number=1)
blocks_since2 = database.get_blocks_since(public_key = member[1],sequence_number=4)
blocks_since3 = database.get_blocks_since(public_key = member[1],sequence_number=4)

for block in blocks_since:
	print block.up