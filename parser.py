import pandas as pd
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

###### CHANGE THESE FIVE LINES 

my_json_url = 'https://results.sos.ga.gov/cdn/results/Georgia/export-2024NovGen.json'
my_url = 'https://results.sos.ga.gov/results/public/Georgia/elections/2024NovGen'
my_source = 'Georgia Secretary of State'
my_title = 'Georgia Election Night Reporting'
my_timezone = 'America/New_York'  # Timezone choices: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

######

response = requests.get(my_json_url)
response_obj = json.loads(response.content)
print(response_obj.keys())

# First, get high-level summary data for this election.
# You will use these in Datawrapper to set the visualization properties. https://developer.datawrapper.de/docs/chart-properties

# Get and prettify the election's date. 
election_date_str = (response_obj['electionDate'])
election_date_obj = datetime.strptime(election_date_str, '%Y-%m-%d')
election_date_prettfied = datetime.strftime(election_date_obj, '%B %-d %Y')

# Get the election's name too
election_name = (response_obj['electionName'])

# Get the timestamp of the last update to the data.
update_string = response_obj['createdAt']

# it's in this format: 2025-01-30T13:59:59.5881725Z
# The Z at the end indicates that this is in UTC, not local time.
# parse it into a datetime object with the correct timezone
update_object= (datetime.fromisoformat(update_string.replace('Z', '+00:00'))
				.astimezone(ZoneInfo(my_timezone)))

# Then parse the datetime object into an easily read date: Nov. 21, 2025 08:59 AM
update_prettified = datetime.strftime(update_object, '%B %d %Y %I:%M %p')

# make a properties dict according to Datawrapper's specs:
 # https://developer.datawrapper.de/docs/chart-properties

properties_object = {
	'title' : my_title,
	'describe' : {
		'intro' : 'Last Updated ' + update_prettified,
		'source_name' : my_source,
		'source_url' : my_url,
		'description' : election_name + ' ' + election_date_prettfied,
		'aria-description' : 'Bar graph of ' + my_title + ', last updated at ' + update_prettified + '.  Original data at ' + my_url
	}
}

# Write that dict as a json file in github
# Let's give the file a good descriptive name & date

outfile_name = election_date_str + ' ' + election_name + '.json'
with open(outfile_name, 'w') as f:
	json.dump(properties_object, f, indent=4)


# Use Pandas to transform the list of ballot options in the nested object into a two-dimensional table 
# Pandas convention for this object is a dataframe, aka df. 
# Think of a df as a simple table with rows and columns, for this exercise.

df = pd.json_normalize(
	response_obj, 
	# Make a table out of the list of objects that's at resp_obj['results']['ballotItems']['ballotOptions']
	# This will create a row for every object in this list
	record_path = ['results', 'ballotItems','ballotOptions'],
	# But also, keep these fields from the parent records
	meta = [
		['results','ballotItems', 'id'],
		['results','ballotItems', 'name']
		]
	)

# We've got the data. Now parse it into a four-column csv for Datawrapper:
# The four columns should be:

# The name of each contest and the number of counties reporting so far (President, X of Y counties reporting)
# A label that includes each candidate's name and the running total of votes they have (Jane Doe, 493,203)
# A running percentage of votes each candidate has (35%)
# Each candidate's political party (Rep)

# Add a new column in the dataframe for the sum total of votes recieved so far in a contest
# Groupby works just like it does in Excel: For a given contest, add up all the votes recieved by all the candidates
df['sum_of_contest'] = df.groupby("results.ballotItems.id")["voteCount"].transform("sum")


# Add a new column that expresses the candidate's vote count as a percent of the whole
df['percent_of_contest'] = (df['voteCount'] / df['sum_of_contest']) * 100

# Add a new column that puts the candidate's name and their vote count in one column
# and wrap it in some html to make it look good in Datawrapper
df['label'] = '<b>' + df['name'] + '</b><br>' + df['voteCount'].map("{:,}".format).astype(str) + ' votes'

# The number of precincts or counties reporting so far isn't in our table. 
# We gotta retreive it from the resp_obj Python dict
# Precincts reporting is in a county-by-county list

counties_df = pd.json_normalize(
	response_obj,
	# This path traverses down to a list of every county
	# Within each county, there's a dict of ballot items
	record_path = ['localResults', 'ballotItems'],
	meta = [['localResults','name']]
	)

# Two items are interesting in each county's record: precinctsParticipating and precinctsReporting
# so go through every county, and for each contest (president, House District 5, etc), 
# sum the number of precincts particpating in and reporting from that contest.

reporting_df = counties_df.groupby('name')[['precinctsParticipating', 'precinctsReporting']].sum()



#  NOTE ! For local races, contest ids and contest names *can* repeat; neither are unique
#  For example, both County A and County B can have
 # a contest called "County Commission Chair" where ballot_item id == 1

# But for federal & state & statewide races, I don't think a ballot_item id could equal 1? 
#  It seems like state and federal ballot_item ids have more digits? Not sure. 
# So, I'll groupby ballot_item name. 



# Join the reporting_df to the main df on the shared field
# Like, the two tables have a column in common, the name of the ballot item 


# the shared columns have different names
# in df it's called 'result.ballotItems.name', in reporting_df, it's 'name' 
# left join means "keep all rows from the first table; leave out any extra rows found in  the second table"

joined = df.merge(reporting_df, left_on='results.ballotItems.name', right_on='name', how='left')

# joined.to_csv('joined.csv')



#Then drop the columns Datawrapper doesn't need
joined = joined.drop(columns = ['groupResults', 'precinctResults', 'ballotOrder', 'id', 'sum_of_contest', 'name', 'voteCount', 'results.ballotItems.id'])

# # publish the output to your Github repo as a .csv.
#  let's give it a good descriptive name
state_and_federal_outfile_name = election_date_str + ' ' + election_name + '-state-federal' + '.csv'
joined.to_csv('state_and_federal_outfile_name')

