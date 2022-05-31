#! /usr/bin/env python3

"""
Sherlock: Find Usernames Across Social Networks Module

This module contains the main logic to search for usernames at social
networks.
"""

import csv
import os
import platform
import QueryStatus
from result import QueryResult
from notify import QueryNotifyPrint
from sites  import SitesInformation

module_name = "Sherlock: Find Usernames Across Social Networks"
__version__ = "0.14.0"




class SherlockFuturesSession(FuturesSession):
    def request(self, method, url, hooks={}, *args, **kwargs):
        """Request URL.

        This extends the FuturesSession request method to calculate a response
        time metric to each requ

        It is taken (almost) directly from the following Stack Overflow answer:
        https://github.com/ross/requests-
                        action="store",
                        help="One or more usernames to check with social networks."
                        )
    parser.add_argument("--browse", "-b",
                        action="store_true", dest="browse", default=False,
                        help="Browse to all results on default browser.")

    parser.add_argument("--local", "-l",
                        action="store_true", default=False,
                        help="Force the use of the local data.json file.")

    args = parser.parse_args()

    # Check for newer version of Sherlock. If it exists, let the user know about it
    try:
        r = requests.get("https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock/sherlock.py")

        remote_version = str(re.findall('__version__ = "(.*)"', r.text)[0])
        local_version = __version__

        if remote_version != local_version:
            print("Update Available!\n" +
                  f"You are running version {local_version}. Version {remote_version} is available at https://git.io/sherlock")

    except Exception as error:
        print(f"A problem occurred while checking for an update: {error}")


    # Argument check
    # TODO regex check on args.proxy
    if args.tor and (args.proxy is not None):
        raise Exception("Tor and Proxy cannot be set at the same time.")

    # Make prompts
    if args.proxy is not None:
        print("Using the proxy: " + args.proxy)

    if args.tor or args.unique_tor:
        print("Using Tor to make requests")
        print("Warning: some websites might refuse connecting over Tor, so note that using this option might increase connection errors.")

    # Check if both output methods are entered as input.
    if args.output is not None and args.folderoutput is not None:
        print("You can only use one of the output methods.")
        sys.exit(1)

    # Check validity for single username output.
    if args.output is not None and len(args.username) != 1:
        print("You can only use --output with a single username")
        sys.exit(1)


    # Create object with all information about sites we are aware of.
    try:
        if args.local:
            sites = SitesInformation(os.path.join(os.path.dirname(__file__), "resources/data.json"))
        else:
            sites = SitesInformation(args.json_file)
    except Exception as error:
        print(f"ERROR:  {error}")
        sys.exit(1)

    # Create original dictionary from SitesInformation() object.
    # Eventually, the rest of the code will be updated to use the new object
    # directly, but this will glue the two pieces together.
    site_data_all = {}
    for site in sites:
        site_data_all[site.name] = site.information

    if args.site_list is None:
        # Not desired to look at a sub-set of sites
        site_data = site_data_all
    else:
        # User desires to selectively run queries on a sub-set of the site list.

        # Make sure that the sites are supported & build up pruned site database.
        site_data = {}
        site_missing = []
        for site in args.site_list:
            counter = 0
            for existing_site in site_data_all:
                if site.lower() == existing_site.lower():
                    site_data[existing_site] = site_data_all[existing_site]
                    counter += 1
            if counter == 0:
                # Build up list of sites not supported for future error message.
                site_missing.append(f"'{site}'")

        if site_missing:
            print(f"Error: Desired sites not found: {', '.join(site_missing)}.")

        if not site_data:
            sys.exit(1)

    # Create notify object for query results.
    query_notify = QueryNotifyPrint(result=None,
                                    verbose=args.verbose,
                                    print_all=args.print_all,
                                    color=not args.no_color)

    # Run report on all specified users.
    for username in args.username:
        results = sherlock(username,
                           site_data,
                           query_notify,
                           tor=args.tor,
                           unique_tor=args.unique_tor,
                           proxy=args.proxy,
                           timeout=args.timeout)

        if args.output:
            result_file = args.output
        elif args.folderoutput:
            # The usernames results should be stored in a targeted folder.
            # If the folder doesn't exist, create it first
            os.makedirs(args.folderoutput, exist_ok=True)
            result_file = os.path.join(args.folderoutput, f"{username}.txt")
        else:
            result_file = f"{username}.txt"

        with open(result_file, "w", encoding="utf-8") as file:
            exists_counter = 0
            for website_name in results:
                dictionary = results[website_name]
                if dictionary.get("status").status == QueryStatus.CLAIMED:
                    exists_counter += 1
                    file.write(dictionary["url_user"] + "\n")
            file.write(f"Total Websites Username Detected On : {exists_counter}\n")

        if args.csv:
            result_file = f"{username}.csv"
            if args.folderoutput:
                # The usernames results should be stored in a targeted folder.
                # If the folder doesn't exist, create it first
                os.makedirs(args.folderoutput, exist_ok=True)
                result_file = os.path.join(args.folderoutput, result_file)

            with open(result_file, "w", newline='', encoding="utf-8") as csv_report:
                writer = csv.writer(csv_report)
                writer.writerow(["username",
                                 "name",
                                 "url_main",
                                 "url_user",
                                 "exists",
                                 "http_status",
                                 "response_time_s"
                                 ]
                                )
                for site in results:
                    response_time_s = results[site]["status"].query_time
                    if response_time_s is None:
                        response_time_s = ""
                    writer.writerow([username,
                                     site,
                                     results[site]["url_main"],
                                     results[site]["url_user"],
                                     str(results[site]["status"].status),
                                     results[site]["http_status"],
                                     response_time_s
                                     ]
                                    )
        print()


if __name__ == "__main__":
    main()
