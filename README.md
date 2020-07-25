# gtechna-idor
gtechna online parking ticket payment product as used by Parking Enforcement Services in Australia + NZ contains a trivial IDOR 
that allows an attacker to view PII about every parking infringement ticket issued including timestamp + GPS location, car registration, 
photos of the vehicle, details of any appeal etc.

Have tried a few times to disclose to PES, whatever. Have also reached out to gtechna. Hundreds of thousands of drivers impacted in Australia.

## Usage

Example - search for every ticket serial between 100000001 and 100000011 with 32 threads concurrently, saving in the folder tickets/
`parking.py --min 100000001 --max 100000011 --destination tickets/ --threads 32`

* Aussie tickets starting at 100000001 and going at least as far as 108400000
* NZ tickets starting looking around 751000000

## Note

You may be able to trigger an application level DOS by requesting tickets on too many threads. It's possible that the DOS may last for 
days in some cases. From memory I think it affects the image endpoint, but I've lost interest in poking at this. You have been warned.

## Disclaimer

This POC was written to confirm the existence of a security / privacy issue that I am personally impacted by, and for the purpose of
disclosing the issue to the system owners / forming the basis of a privacy complaint to OAIC. After receiving nil response from Parking
Enforcement Services I have released it in the interest of transparency. 

I do hold the opinion that this company has a dogshit unethical business model, but that's a separate issue.
