Intro
=====

**secret-santa** can help you manage a list of secret santa participants by
randomly assigning pairings and sending emails. It can avoid pairing
couples to their significant other, and allows custom email messages to be
specified.

Dependencies
------------

Non-core dependencies:

* pytz

To installed the needed dependencies:

    pip install -r ./requirements.txt

Usage
-----

Copy config.yml.template to config.yml and enter in the connection details
for your outgoing mail server. Modify the participants and couples lists and
the email message if you wish.

    cd secret-santa/
    cp config.yml.template config.yml

Here is the example configuration unchanged:

    # Required to connect to your outgoing mail server. Example for using gmail:
    # gmail
    SMTP_SERVER: smtp.gmail.com
    SMTP_PORT: 587
    USERNAME: you@gmail.com
    PASSWORD: "your-password"

    TIMEZONE: 'US/Eastern'

    PARTICIPANTS:
      - name: Chad
        email: chad@somewhere.net
        wish_list: amazon.com/something/sommething
        dont_pair:
        - Jen
      - name: Jen
        email: jen@gmail.net
        wish_list: amazon.com/something/sommething
        dont_pair:
          - Chad
      - name: Bill
        email: Bill@somedomain.net
        wish_list: amazon.com/something/sommething
        dont_pair:
          - Chad
      - name: Sharon
        email: Sharon@hi.org
        wish_list: amazon.com/something/sommething
        dont_pair:
          - Bill

    # From address should be the organizer in case participants have any questions
    FROM: secret-santa@gmail.net

    # Both SUBJECT and MESSAGE can include variable substitution for the
    # "santa" and "santee" as well "wish_list"
    SUBJECT: Your secret santa recipient is {santee}
    MESSAGE: "Dear {santa},


    This year you are {santee}'s Secret Santa!. Ho Ho Ho!


    The maximum spending limit is 50.00


    Provided wish list information:


        {wish_list}

    "

Once configured, call secret-santa:

    $ ./secret_santa.py

Calling secret-santa without arguments will output a test pairing of
participants.

        Test pairings:

        Chad   ---> Bill
        Jen    ---> Sharon
        Bill   ---> Chad
        Sharon ---> Jen

To send out emails with new pairings, call with the --send argument:

    $ ./secret_santa.py --send
