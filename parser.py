import pandas as pd
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import os

###### CHANGE THESE FIVE LINES 

my_json_url = 'https://results.sos.ga.gov/cdn/results/Georgia/export-06162026GeneralPrimaryRunoff.json'
my_url = 'https://results.sos.ga.gov/results/public/Georgia/elections/06162026GeneralPrimaryRunoff' # The source url for your graph footnote
my_source = 'Georgia Secretary of State'
my_title = 'Georgia Election Night Reporting'
my_timezone = 'America/New_York'  # Timezone choices: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones


######

# These three lines call the running vote count and parse it into a Python dict.

response = requests.get(my_json_url)
response_obj = json.loads(response.content)
print(response_obj.keys())



#### politicalParty is not consistently filled in for partisan races; party is compounded with name sometimes.
#####
##### And when party is compounded with name, the formatting is inconsistent: '- Dem', '(Dem)'

#### So ... hm, let's try and fill in party but DONT put any party in judicial races.
#### This requires testing.
#### Don't run this part unless u have to


# dem_flags = ['(DEM)', '- DEM']
# rep_flags = ['(REP)', '- REP']
# lib_flags = ['(LIB)' '-LIB']
# grn_flags = ['(GRN)', '-GRN']

# results_ballot_items = response_obj['results']['ballotItems']
# for i in range(len(results_ballot_items)):
# 	# print('***')
# 	people = (results_ballot_items[i]['ballotOptions'])
# 	for j in range(len(people)):
# 		# print(people[j]['name'], people[j]['politicalParty'])
# 		if (people[j]['politicalParty']) == '':
# 			# print('+++++')
# 			# print(people[j]['name'], people[j]['politicalParty'])
# 			party = ''
# 			if any(sub in people[j]['name'].upper() for sub in dem_flags):
# 				people[j]['politicalParty'] = 'Dem'
# 			elif any(sub in people[j]['name'].upper() for sub in rep_flags):
# 				people[j]['politicalParty'] = 'Rep'
# 			elif any(sub in people[j]['name'].upper() for sub in lib_flags):
# 				people[j]['politicalParty'] = 'Lib'
# 			elif any(sub in people[j]['name'].upper() for sub in grn_flags):
# 				people[j]['politicalParty'] = 'Grn'
# 			else:
# 				pass
# 		# print(people[j]['name'], people[j]['politicalParty'])


# local_results_ballot_items_list = response_obj['localResults']

# for county in local_results_ballot_items_list:
# 	ballot_items = county['ballotItems']
# 	for i in range(len(ballot_items)):
# 		people = ballot_items[i]['ballotOptions']
# 		for j in range(len(people)):
# 			# print(people[j]['name'])
# 			if (people[j]['politicalParty']) == '':
# 				# print('+++++')
# 				# print(people[j]['name'], people[j]['politicalParty'])
# 				party = ''
# 				if any(sub in people[j]['name'].upper() for sub in dem_flags):
# 					people[j]['politicalParty'] = 'Dem'
# 				elif any(sub in people[j]['name'].upper() for sub in rep_flags):
# 					people[j]['politicalParty'] = 'Rep'
# 				elif any(sub in people[j]['name'].upper() for sub in lib_flags):
# 					people[j]['politicalParty'] = 'Lib'
# 				elif any(sub in people[j]['name'].upper() for sub in grn_flags):
# 					people[j]['politicalParty'] = 'Grn'
# 				else:
# 					pass
# 			# print(people[j]['name'], people[j]['politicalParty'])


############### PART 1: Get data properties ###############

# First, get high-level summary data for this election: Title, date & timestamp
# You will use these in Datawrapper to set the visualization properties
# https://developer.datawrapper.de/docs/chart-properties

# Get the election's name.  It'll be something like "General election"
election_name = (response_obj['electionName'])

# Get and prettify the election's date. 
election_date_str = (response_obj['electionDate'])
election_date_obj = datetime.strptime(election_date_str, '%Y-%m-%d')
election_date_prettified = datetime.strftime(election_date_obj, '%B %-d %Y')

# Get the timestamp of the last update to the data.
update_string = response_obj['createdAt']

# It's a string in this format: 2025-01-30T13:59:59.5881725Z
# The Z at the end indicates that this is in UTC, not local time.
# Parse the string into a datetime object and tell it your timezone
update_object= (datetime.fromisoformat(update_string.replace('Z', '+00:00'))
				.astimezone(ZoneInfo(my_timezone)))

# Then parse the timezone-aware object into a human-readable date: Nov. 21, 2025 08:59 AM
update_prettified = datetime.strftime(update_object, '%B %d, %Y %-I:%M %p')

# Make a properties dict according to Datawrapper's specs:
# https://developer.datawrapper.de/docs/chart-properties

properties_object = {
	'title' : my_title + ' ' + election_date_prettified,
	'describe' : {
		'intro' : 'Last Updated ' + update_prettified,
		'source-name' : my_source,
		'source-url' : my_url,
		# 'description' : election_name + ' ' + election_date_prettfied,
		'aria-description' : 'Bar graph of ' + my_title + ', last updated at ' + update_prettified + '.  Original data at ' + my_url
	}
}

# Write that dict as a json file in github
# Let's give the file a good descriptive name & date

json_outfile_name = election_date_str + '/' + election_date_str + ' ' + election_name + '.json'

out_dir = election_date_str
if not os.path.exists(out_dir):
	os.makedirs(out_dir)

with open(json_outfile_name, 'w') as f:
	json.dump(properties_object, f, indent=4) 

# ############# PART 1 DONE ! Graph properties acquired & parsed into Datawrapper format. ################

# ############# PART 2: Get results for federal & state races #######################

# # As of this writing, Enhanced Voting's json format in Georgia is this:
# # https://github.com/maggie-lee/election-night-results-tutorial/blob/7f5820d6e756cea847aa3d4ef5722c9e7c479fcd/Georgia%20Media%20JSON%20Guide.pdf

# # Federal & State ballot_items are in one portion of the json
# # Local ballot_items, including those that cross county lines, are in the other portion.
# # Let's do federal & state first.

# # In this json, a "ballot item" is a race or a contest.  Like "President" or "U.S. House District 1 Republican" (for primaries)
# # In this json, a "ballot option" is a candidate's name or a yes/no for referenda.

# # Use Pandas to access the list of federal & state ballot items, candidates, parties and vote count. It's down in the nested object. 
# # Pandas convention for this object you create is a "dataframe," aka "df". 
# # Think of a df as a simple table with rows and columns, for this exercise.

df = pd.json_normalize(
	response_obj, 
	# Make a table out of the list of objects that's at resp_obj['results']['ballotItems']['ballotOptions']
	# This will create a row for every object in this list
	record_path = ['results', 'ballotItems','ballotOptions'],
	# But also, keep these fields from the parent records
	meta = [
		['results','ballotItems', 'id'],
		['results','ballotItems', 'name'],
		['results','ballotItems', 'ballotOrder']
		]
	)

# We've got the data. 
# There is a row for every candidate. 
# Now parse it into a four-column csv for Datawrapper
# The columns will be:
# 
# - A label that includes each candidate's name and the running total of votes they have (Jane Doe, 493,203)
# - A running percentage of votes each candidate has
# - Each candidate's political party
# - The name of each ballot_item and the number of counties reporting so far (President, X of Y precincts reporting)


# Add a new column in the dataframe for the sum total of votes recieved so far in a ballot_item
# Groupby works just like it does in Excel: For a given ballot_item, add up all the votes recieved by all the candidates
df['sum_of_ballot_item'] = df.groupby("results.ballotItems.id")["voteCount"].transform("sum")


# Add a new column that expresses the candidate's vote count as a percent of the whole
df['percent_of_ballot_item'] = (df['voteCount'] / df['sum_of_ballot_item']) * 100

# Add a new column that puts the candidate's name and their vote count in one column
# and wrap it in some html to make it look good in Datawrapper
df['label'] = '<b>' + df['name'] + '</b><br>' + df['voteCount'].map("{:,}".format).astype(str) + ' votes'

# print( 'number of ballot_items: ' + str(df['results.ballotItems.name'].nunique()))

# The number of precincts or counties reporting so far isn't in our table. 
# We gotta retreive it from the resp_obj Python dict
# Precincts reporting is in a county-by-county list

counties_df = pd.json_normalize(
	response_obj,
	# This path traverses down to a list of every county
	# Within each county, there's a dict of ballot items
	record_path = ['localResults', 'ballotItems'], # grab the ballot items
	meta = [['localResults','name']] # in each row, also keep the county name from the parent level
	)


# Two items are interesting in each county's record: precinctsParticipating and precinctsReporting
# so go through every county, and for each ballot_item (president, House District 5, etc), 
# sum the number of precincts particpating in and reporting from that ballot_item.

reporting_df = counties_df.groupby('id', as_index=False)[['precinctsParticipating', 'precinctsReporting']].sum()

# # # Howver I only want the records for state/federal ballot_items, each of which has a unique id. 
# # So Ill keep rows in reporting_df where the column 'id' has a match in df['results.ballotItems.id']

filtered_df = reporting_df[reporting_df['id'].isin(df['results.ballotItems.id'])]


## Do some verification here
# check the number of state/federal ballot_items you found: 
# print('number of ballot_items: ' + str(df['results.ballotItems.name'].nunique()))

# # then check the number of state/federal ballot_items for which you found precincts
# print('number of ballot_items: ' + str(len(filtered_df)))

# They should be equal !



# So, now, a sample record in df will look like this:
# 
# id                                                                          2
# name                                                   Kamala D. Harris (Dem)
# ballotOrder                                                                 2
# voteCount                                                             2548017
# politicalParty                                                            Dem
# groupResults                [{'groupName': 'Election Day', 'voteCount': 55...
# precinctResults                                                          None
# results.ballotItems.id                                                   5100
# results.ballotItems.name                                  President of the US
# sum_of_ballot_item                                                    5250047
# percent_of_ballot_item                                              48.533223
# label                        <b>Kamala D. Harris (Dem)</b><br>2,548,017 votes


# A sample record in filtered_df will look like this:
# id                        5100
# precinctsParticipating    2701
# precinctsReporting        2701


# These two tables have the id 5100 in common
# We can merge the two tables on that shared id.
# Every row  that has id 5100 (Harris, Trump, Oliver, Stein) will pull in precinct data from rows that also have id 5100.
# Pandas' merge function has some built-in checks to make sure each ballot item gets a precinct report
# And that each precinct report gets attached to one or more contests.

joined = pd.merge(
	df, # envision this as a table on the left
	filtered_df, # envision this as a table on the right
	left_on='results.ballotItems.id', # in the left table, this is the id column
	right_on='id',  # in the right table, this is the id colum
	how='outer', # preserve all rows, even those without a match
	indicator = True, # add an indicator column that shows whether a record was in the right, left or both tables.  We want all "both"
	validate='many_to_one') # Check if merge keys are unique in the right table 

# If there are any problematic rows, print them
# And stop the program.  Something is wrong. 

problems = joined[joined['_merge'] != 'both']
if not problems.empty:
	print(problems)
	raise(ValueError(f"Found {len(bad_rows)} unmatched rows"))

# But if everything's ok, 
# sort the table in the order it needs to go in Datawrapper.
# in this json, that's ballot order of the ballot item, then ballot order of the candidate
sorted_df = joined.sort_values(by=['results.ballotItems.ballotOrder', 'ballotOrder'])

# print(sorted_df.iloc[1])
# And delete (drop) the columns that Datawrapper doesn't need

#Then drop the columns Datawrapper doesn't need. 
simplified_df = sorted_df.drop(columns = ['id_x', 
	'name',
	'ballotOrder',
	'voteCount',
	'groupResults', 
	'precinctResults', 
	'results.ballotItems.ballotOrder',
	'sum_of_ballot_item',
	'id_y',
	'_merge'])

simplified_df.rename(columns={'results.ballotItems.name':'contest_name'}, inplace=True)

simplified_df['contest_name'] = simplified_df['contest_name'] + '<br>' + \
	simplified_df['precinctsReporting'].astype(str) + ' of ' + \
	simplified_df['precinctsParticipating'].astype(str) + ' precincts reporting'


# print(simplified_df.iloc[0])

# # # publish the output to your Github repo as a .csv.
# #  let's give it a good descriptive name
state_and_federal_outfile_name = election_date_str + '/' + election_date_str + ' ' + election_name + '-state-federal' + '.csv'
simplified_df.to_csv(state_and_federal_outfile_name)


# ############# PART 2 COMPLETE! State & federal contests fetched & parsed for Datawrapper #######################

############# PART 3: Get results for local races #######################

# Local races are in another part of response_obj
# Let's make a local_df

# The editor wants coverage of six counties
# Each county should get its own embed code
# Each county should include the following races:

# Any state House/Senate ballot items that touch the couny
# Any DA ballot items that touches the county
# Any truly county- or city-level items like school board, coroner, sheriff,etc.



counties = response_obj['localResults']
# print(type(counties))

for county in counties:
	local_df = pd.json_normalize(
		county,
		record_path = ['ballotItems', 'ballotOptions'],
		meta= [
			['name'],
			['ballotItems', 'name'],
			['ballotItems', 'id'],
			['ballotItems', 'precinctsParticipating'],
			['ballotItems', 'precinctsReporting'],
			],
		meta_prefix = 'county_'
		)
	# print(local_df.iloc[0])
	# print(local_df.head())
	# print(len(local_df))
	# But this is all races in the county, including the ones the boss doesn't want: federal & statewide.
	# I don't see any flag in the data for federal & statewide.
	# I don't see any pattern to the ID numbers assigned to different levels of government
	# I think I have to filter by the name of the contest. 
	# ie, just exclude the ones she doesn't want
	# This is not great but here goes:

	# 
	exclude_list = ['US ', 'GOVERNOR', 'SECRETARY', 'AGRICULTURE', 
					'ATTORNEY GENERAL', 'INSURANCE', 'SUPERINTENDENT', 'LABOR',
					'PUBLIC SERVICE', 'SUPREME', 'APPEALS', 'STATEWIDE', 'CONSTITUTIONAL', 'PSC ', 'PARTY QUESTION']

	filtered_local_df = local_df[~local_df['county_ballotItems.name'].str.contains('|'.join(exclude_list), case=False, na=False)].copy()

	# print(filtered_local_df.iloc[0])

	# print(len(filtered_local_df))
	# for index, row in filtered_local_df.iterrows():
	# 	print(row['name'], row['county_ballotItems.name'])
	# print(df.iloc[0])
	#  ok very good. 

	# Now, if it's a State Legislator/District Attorney, I  want full results in that race, across county boundaries
	# not just the parts that are in the county. 

	# Which I have to get from the previous df!

	# So, if county_ballotItems.id in previous df:
	# pull in results from previous df 


	# has_overlap = sorted_df['results.ballotItems.id'].isin(filtered_local_df['county_ballotItems.id'])
	# print(has_overlap)

	# Pull the ids of all ballot items from the state list that touch this county

	shared_ids = set(sorted_df['results.ballotItems.id']) & set(filtered_local_df['county_ballotItems.id'])
	# print(shared_ids)

	# Then make a df of just those cross-county ballot items.
	# This is state legislators and DAs
	# print(simplified_df.iloc[0])

	cross_county_ballot_items = simplified_df[simplified_df['results.ballotItems.id'].isin(list(shared_ids))]
	# print(cross_county_ballot_items.iloc[0])


	# for index, row in cross_county_ballot_items.iterrows():
	# 	print(row['label'], row['contest_name'])

	# ok and remove those guys from filtered_local_df; let them stay in cross_county_ballot_items for a second
	locals_only_df = filtered_local_df[~filtered_local_df['county_ballotItems.id'].isin(list(shared_ids))].copy()


	# print(locals_only_df.iloc[0])
	# print(len(locals_only_df))
	# for index, row in locals_only_df.iterrows():
	# 	print(row['name'], row['county_ballotItems.name'], row['voteCount'])

	# Now the groupby stuff 
	locals_only_df['sum_of_ballot_item'] =locals_only_df.groupby("county_ballotItems.id")["voteCount"].transform("sum")
	
	# for index, row in locals_only_df.iterrows():
	# 	print(row['name'], row['county_ballotItems.name'], row['voteCount'], row['sum_of_ballot_item'])

	locals_only_df['percent_of_ballot_item'] = (locals_only_df['voteCount'] / locals_only_df['sum_of_ballot_item']) * 100
	# # for index, row in locals_only_df.iterrows():
	# 	print(row['name'], row['county_ballotItems.name'], row['voteCount'], row['sum_of_ballot_item'], row['percent_of_ballot_item'])

	# precincts participatin & precincts reporting are already in this data; we don't have to fetch it from elsewhere.
	# but we do have to get it in datawrapper format:
	locals_only_df['label'] = '<b>' + locals_only_df['name'] + '</b><br>' + locals_only_df['voteCount'].map("{:,}".format).astype(str) + ' votes'
	# print(locals_only_df.iloc[0])

	sorted_locals_only = locals_only_df.sort_values(by=['id', 'ballotOrder'])
	# for index, row in sorted_locals_only.iterrows():
	# 	print(row['county_ballotItems.name'], row['label'])

	sorted_locals_only['contest_name'] = sorted_locals_only['county_name'] + ': ' + sorted_locals_only['county_ballotItems.name']

	# now drop the columns datawrapper doesn't need
	simplified_locals_only = sorted_locals_only.drop( columns = [
		'id',
		'name',
		'ballotOrder',
		'voteCount',
		'county_ballotItems.id',
		'sum_of_ballot_item',
		'groupResults',
		'precinctResults',
		'county_name',
		'county_ballotItems.name'
		])

	simplified_locals_only = simplified_locals_only.rename(columns={'county_ballotItems.precinctsParticipating':'precinctsParticipating'})
	simplified_locals_only = simplified_locals_only.rename(columns={'county_ballotItems.precinctsReporting':'precinctsReporting'})
	cross_county_ballot_items.drop(columns =['results.ballotItems.id'])


	# print(cross_county_ballot_items.iloc[0])
	# sorted_cross_county_ballot_items = cross_county_ballot_items.sort(values(by=[]'results.ballotItems.id'))
	# cleanup
	county_combined = pd.concat([cross_county_ballot_items, simplified_locals_only], ignore_index=True)
	#  some of the party field are blank, even if the party is indicated in the person's name.

	county_combined['contest_name'] = county_combined.apply(
		lambda row: (
			row['contest_name']
			if '<br>' in row['contest_name']
			else row['contest_name'] + '<br>' + str(row['precinctsReporting']) + ' of ' + str(row['precinctsParticipating']) + ' precincts reporting'),
		axis=1
		)


	county_filename = election_date_str + '/' + election_date_str + ' ' + election_name + ' ' + county['name'] +'.csv'
	counties_to_keep = ['chatham', 'glynn', 'mcintosh', 'liberty', 'bryan', 'camden']
	if any(sub in county_filename.lower() for sub in counties_to_keep):
		county_combined.to_csv(county_filename)


