# sigtech-python
Sigtech Framework API Python Wrapper


## Installation

Install from source with:

```sh
python setup.py install
```

### Requirements

-   Python 3.6+

## Usage

First set the environment variable 'SIGTECH_API_KEY' to your API token.

```python
import os
os.environ['SIGTECH_API_KEY'] = # YOUR API KEY #
```

Once the variables are set we can use the API python wrapper.

There are two options for interacting with the objects.

One option is a higher level object based interface. An example is given below.

```python
# imports
import sigtech.api as sig
import datetime as dtm

# initialize environment and session
sig.init()

# create rolling future strategies

vg_future = sig.RollingFutureStrategy(contract_code='VG', contract_sector='INDEX', rolling_rule='front',
                                      front_offset='-4:-1')
es_future = sig.RollingFutureStrategy(contract_code='ES', contract_sector='INDEX')

# create baskets
basket = sig.BasketStrategy(constituent_names=[vg_future.name, es_future.name], weights=[0.5, 0.5],
                            rebalance_frequency='EOM', currency='USD', start_date=dtm.date(2020, 2, 1))

# retrieve the strategy history
print(basket.history())
```

Alternatively, the API requests can be made directly via the client. An example is given below.

```python
import sigtech.api as sig

# Setup Client

client = sig.Client()

# Create session

session = client.sessions.create()
session_id = session.session_id
print(f'session id : {session_id}')

# New Rolling Future Strategy Object

rfs_object = client.strategies.futures.rolling.create(
            session_id=session_id, identifier='ES INDEX',
)
object_id = rfs_object.object_id
print(f'object id : {object_id}')

# Query object status
object_state = client.query_object(session_id, object_id)
print(f'object state : {object_state}')

# wait for completion
rfs_object.wait_for_object_status()

# Retrieve history
history = client.data.history.get(session_id=session_id, object_id=object_id).history
print(f'Rolling Future History : {history}')
```

### Logging

The library emits details of individual API requests to the `debug` log level.

