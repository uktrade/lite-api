## API Reference


### Drafts
**Draft DTO Structure**
<br> Last Updated 15/5/2019
<br> requires USER-ID header
<pre>
{
    "id":[UUID]
    "name":[free text]
    "control_code":[free text]
    "activity":[free text]
    "usage":[free text]
    "destination":[free text]
}
</pre>

Endpoints for retrieving, creating and updating drafts.

<table>
    <tr>
        <th>Method</th><th>URL</th><th>Header</th><th>Body</th><th>Response <br> Codes</th><th>Details</th>
    </tr>
    <!–– Drafts ––>
    <tr>
        <td>GET</td>
        <td>/drafts/</td>
        <td>?</td>
        <td>Request:  None <br> Response: List of DTOs </td>
        <td>200</td>
        <td>Returns all drafts</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>drafts/{id}/</td>
        <td>?</td>
        <td>Request:  None <br> Response: Single DTO </td>
        <td>200   <br>
            404
        </td>
        <td>returns details of a specific draft</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/drafts/</td>
        <td>?</td>
        <td>Request:  DTO Structure <br>
        (without ID)
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a draft </td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/drafts/{id}</td>
        <td>?</td>
        <td>Request:  DTO Structure <br>
        (all elements optional except ID )
        </td>
        <td>200 <br> 404 </td>
        <td> updates the draft(ref. draft_id)  <br>
             with any combination of the  <br>
             updatable fields: name,  <br> 
             control_code, activity,  <br>
             usage, destination.
        </td>
    </tr>
    <tr>
        <td>DELETE</td>
        <td>drafts/{id}/</td>
        <td>?</td>
        <td>None</td>
        <td>200   <br>
            404
        </td>
        <td>Deletes draft with specified id</td>
    </tr>
</table>

example POST /drafts/:
<pre>
{
    "name":"First sample draft",
    "control_code":"test1",
    "activity":"test2",
    "usage":"test3",
    "destination":"test4"
}
</pre>
sample POST /drafts/ response:
<pre>
{
  "draft": {
    "id": "7ece1b1d-453c-440b-b877-1e337c66839a",
    "name": "First sample draft",
    "organisation": "71f3da6b-7b89-4ffc-9d60-a17f8036f331"
  }
}
</pre>
sample GET /drafts/ response:
<pre>
{
  "drafts": [
    {
      "id": "e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4",
      "name": "Second sample draft",
      "activity": null,
      "destination": null,
      "usage": null,
      "organisation": "71f3da6b-7b89-4ffc-9d60-a17f8036f331",
      "created_at": "2019-05-15T14:43:59Z",
      "last_modified_at": "2019-05-15T14:43:59Z"
    }
  ]
}
</pre>
sample GET /drafts/e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4 response:
<pre>
{
  "draft": {
    "id": "e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4",
    "name": "Second sample draft",
    "activity": null,
    "destination": null,
    "usage": null,
    "organisation": "71f3da6b-7b89-4ffc-9d60-a17f8036f331",
    "created_at": "2019-05-15T14:43:59Z",
    "last_modified_at": "2019-05-15T14:43:59Z"
  }
}
</pre>
sample PUT /drafts/e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4/ request:
<pre>
{
	"name": "Renamed name"
}
</pre>
sample PUT /drafts/e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4/ response:
<pre>
{
  "draft": {
    "id": "e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4",
    "name": "Renamed name",
    "activity": null,
    "destination": null,
    "usage": null,
    "organisation": "71f3da6b-7b89-4ffc-9d60-a17f8036f331",
    "created_at": "2019-05-15T14:43:59Z",
    "last_modified_at": "2019-05-15T14:43:59Z"
  }
}
</pre>
sample DELETE /drafts/e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4/ response:
<pre>
{
  "status": "Draft Deleted"
}
</pre>
sample GET /drafts/e9b2576b-6d69-4377-bbdf-2f5d6a7d54c4 response:
<pre>
{
  "detail": "Not found."
}
</pre>

### Applications

**Application DTO Structure**
<br> Last Updated 15/5/2019
<br> requires USER-ID header
<pre>
{
    "id": [UUID]
    "name":[free text] 
    "control_code":[free text] 
    "activity":[free text]
    "usage":[free text]
    "destination":[free text]
    "status":[enum of statuses]
}
</pre>

Endpoints for retrieving, creating and updating applications:

<table>
    <tr>
        <th>Method</th><th>URL</th><th>Header</th><th>Body</th><th>Response <br> Codes</th>
        <th max-width: 30px >Details</th>
    </tr>
    <!–– Applications ––>
    <tr>
        <td>GET</td>
        <td>/applications/</td>
        <td>?</td>
        <td>Request:  None <br> Response: List of DTOs </td>
        <td>200</td>
        <td>Returns all applications</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/applications/{id}/</td>
        <td>?</td>
        <td>Request:  None <br> Response: Single DTO </td>
        <td>200 <br> 404 </td>
        <td>returns application with given id</td>
    </tr>
    <tr>
        <td>POST *parse exception*</td>
        <td>/applications/</td>
        <td>?</td>
        <td>Request:  DTO Structure <br>
        (with valid draft id)
        </td>
        <td>200 <br> 422 </td>
        <td>Requires valid draft id <br>
            Submits application with aforementioned id <br>
        </td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/applications/{id}</td>
        <td>?</td>
        <td>Request:  DTO Structure <br>
        (all elements optional except ID )       
        </td>
        <td>200 <br> 404 </td>
        <td>Updates the application <br>
            with application_id <br>
            with any combination of <br>
            the updatable fields: name, <br>
            control_code, activity, usage,  <br>
            destination, status.</td>
</table>

sample GET /applications/ response:
<pre>
{
  "applications": [
    {
      "id": "7ece1b1d-453c-440b-b877-1e337c66839a",
      "name": "First sample draft",
      "activity": null,
      "destination": null,
      "usage": null,
      "goods": [],
      "created_at": "2019-05-15T14:34:55Z",
      "last_modified_at": "2019-05-15T14:34:55Z",
      "submitted_at": "2019-05-15T14:34:55Z",
      "status": "submitted"
    }
  ]
}
</pre>
sample GET /applications/7ece1b1d-453c-440b-b877-1e337c66839a response:
<pre>
{
  "status": "success",
  "application": {
    "id": "7ece1b1d-453c-440b-b877-1e337c66839a",
    "name": "First sample draft",
    "activity": null,
    "destination": null,
    "usage": null,
    "goods": [],
    "created_at": "2019-05-15T14:34:55Z",
    "last_modified_at": "2019-05-15T14:34:55Z",
    "submitted_at": "2019-05-15T14:34:55Z",
    "status": "submitted"
  }
}
</pre>
example POST /applications/ request:
<pre>
{
	"id":"7ece1b1d-453c-440b-b877-1e337c66839a"
}
</pre>
sample POST /applications/ response:
<pre>
{
  "application": {
    "id": "7ece1b1d-453c-440b-b877-1e337c66839a",
    "name": "First sample draft",
    "activity": null,
    "destination": null,
    "usage": null,
    "goods": [],
    "created_at": "2019-05-15T14:34:55Z",
    "last_modified_at": "2019-05-15T14:34:55Z",
    "submitted_at": "2019-05-15T14:34:55Z",
    "status": "submitted"
  }
}
</pre>
example PUT /applications/7ece1b1d-453c-440b-b877-1e337c66839a/ request:
<pre>
{
	"name":"First renamed"
}
</pre>
example PUT /applications/7ece1b1d-453c-440b-b877-1e337c66839a/ response:
<pre>
{
  "application": {
    "id": "7ece1b1d-453c-440b-b877-1e337c66839a",
    "name": "First renamed",
    "activity": null,
    "destination": null,
    "usage": null,
    "goods": [],
    "created_at": "2019-05-15T14:34:55Z",
    "last_modified_at": "2019-05-15T14:34:55Z",
    "submitted_at": "2019-05-15T14:34:55Z",
    "status": "submitted"
  }
}
</pre>

### Organisations
**Organisation DTO Structure**
<pre>
{
    "id":[UUID],
    "name":[free text],
    "eori_number":[free text], 
    "sic_number":[free text],
    "vat_number":[free text],
    "registration_number":[free text],
    "admin_user_email":[valid email address],
    "user": {             
        "first_name":[free text], 
        "last_name":[free text],
        "email":[valid email address],
        "password":[free text]
	},
    "site": {
        "name":[free text],
        "address":{
            "address_line_1":[free text],
            "postcode":[free text],
            "city":[free text],
            "region":[free text],
            "country":[free text]
        }
    }
}

Endpoints for retrieving, creating and updating organisations.
<table>
    <tr>
        <th>Method</th><th>URL</th><th>Header</th><th>Body</th><th>Response <br> Codes</th><th>Details</th>
    </tr>
    <!–– Organisations ––>
    <tr>
        <td>GET</td>
        <td>/organisations/</td>
        <td>?</td>
        <td>Request:  None <br> Response: List of DTOs </td>
        <td>200</td>
        <td>Returns all organisations</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/organisations/{id}</td>
        <td>?</td>
        <td>Request:  None <br> Response: Single DTO</td>
        <td>200   <br>
            404
        <td>Returns details of a   <br>
        specific organisation</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/organisations/</td>
        <td>?</td>
        <td> Request:  DTO Structure <br>
        (without ID)
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a organisation </td>
    </tr>
</table>

</pre>
example POST /organisations/ request:
<pre>
{
    "id":"UUID-24234",
    "name":"Test Organisation",
    "eori_number":"4646", 
    "sic_number":"43636",
    "vat_number":"43616",
    "registration_number":"4536",
    "admin_user_email":"admin@admin.admin",
	"user":	{             
        "first_name":"First", 
        "last_name":"Last",
        "email":"first@last.com",
        "password":"secret32="
    },
    "site": {
        "name":"Test Site",
        "address":{
            "address_line_1": "addresLine1",
            "postcode":"AA1 2DD",
            "city":"Cty",
            "region":"reg",
            "country":"UK"
        }
    }
}
</pre>
sample POST /organisations/ response:
<pre>
{
  "organisation": {
    "id": "71f3da6b-7b89-4ffc-9d60-a17f8036f331",
    "name": "Luke's test",
    "eori_number": "4646",
    "sic_number": "43636",
    "vat_number": "43636",
    "registration_number": "4536",
    "created_at": "2019-05-15T12:50:35.140974Z",
    "last_modified_at": "2019-05-15T12:50:35.141005Z"
  }
}
</pre>
sample GET /organisations/ response:
<pre>
{
  "organisations": [
    {
      "id": "71f3da6b-7b89-4ffc-9d60-a17f8036f331",
      "name": "Luke's test",
      "eori_number": "4646",
      "sic_number": "43636",
      "vat_number": "43636",
      "registration_number": "4536",
      "primary_site": {
        "id": "921104c6-cca9-4e3e-8e3c-b9d49528ab77",
        "name": "Test Site",
        "address": {
          "id": "d15ab319-9147-42ed-be5c-3a373ca78852",
          "address_line_1": "addresLine1",
          "address_line_2": null,
          "postcode": "AA1 2DD",
          "city": "Cty",
          "region": "reg",
          "country": "UK"
        }
      },
      "created_at": "2019-05-15T12:50:35.140974Z",
      "last_modified_at": "2019-05-15T12:50:35.141005Z"
    }
  ]
}
</pre>
sample GET /organisations/71f3da6b-7b89-4ffc-9d60-a17f8036f331 response:
<pre>
{
  "organisation": {
    "id": "71f3da6b-7b89-4ffc-9d60-a17f8036f331",
    "name": "Luke's test",
    "eori_number": "4646",
    "sic_number": "43636",
    "vat_number": "43636",
    "registration_number": "4536",
    "primary_site": {
      "id": "921104c6-cca9-4e3e-8e3c-b9d49528ab77",
      "name": "Test Site",
      "address": {
        "id": "d15ab319-9147-42ed-be5c-3a373ca78852",
        "address_line_1": "addresLine1",
        "address_line_2": null,
        "postcode": "AA1 2DD",
        "city": "Cty",
        "region": "reg",
        "country": "UK"
      }
    },
    "created_at": "2019-05-15T12:50:35.140974Z",
    "last_modified_at": "2019-05-15T12:50:35.141005Z"
  }
}
</pre>

### Sites
**Sites DTO Structure**
<br> Last Updated 14/5/2019
<pre>
{
    "name":[free text],
    "address":{
        "address_line_1":[free text],
        "address_line_2":[free text],
        "postcode":[free text],
        "city":[free text],
        "region":[free text],
        "country":[free text]
    }               
}
</pre>


Endpoints for retrieving, creating and updating organisations.
<table>
    <tr>
        <th>Method</th><th>URL</th><th>Header</th><th>Body</th><th>Response <br> Codes</th><th>Details</th>
    </tr>
    <!–– Sites ––>
    <tr>
        <td>GET</td>
        <td>/organisations/sites/</td>
        <td>?</td>
        <td>Request:  None <br> Response: List of DTOs </td>
        <td>200</td>
        <td>Returns all sites belonging  <br>
         to the users organisation</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/organisations/sites/{id}</td>
        <td>?</td>
        <td>Request:  None <br> Response: Single DTO</td>
        <td>200   <br>
            404
        </td>
        <td>Returns details of <br>
        a specific site</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/organisations/</td>
        <td>?</td>
        <td>Request:  DTO Structure <br>
        (without ID)
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a organisation </td>
    </tr>
</table>
error 500 on PUT /organisations/sites/921104c6-cca9-4e3e-8e3c-b9d49528ab77/<br />
sample GET /organisations/sites/ response
<pre>
{
  "sites": [
    {
      "id": "921104c6-cca9-4e3e-8e3c-b9d49528ab77",
      "name": "Test Site",
      "address": {
        "id": "d15ab319-9147-42ed-be5c-3a373ca78852",
        "address_line_1": "addresLine1",
        "address_line_2": null,
        "postcode": "AA1 2DD",
        "city": "Cty",
        "region": "reg",
        "country": "UK"
      }
    }
  ]
}
</pre>
sample GET /organisations/sites/921104c6-cca9-4e3e-8e3c-b9d49528ab77/ response
<pre>
{
  "site": {
    "id": "921104c6-cca9-4e3e-8e3c-b9d49528ab77",
    "name": "Test Site",
    "address": {
      "id": "d15ab319-9147-42ed-be5c-3a373ca78852",
      "address_line_1": "addresLine1",
      "address_line_2": null,
      "postcode": "AA1 2DD",
      "city": "Cty",
      "region": "reg",
      "country": "UK"
    }
  }
}
</pre>
sample POST /organisations/sites/ request:
<pre>
{
	"name": "Test Site 2",
	"address": {
		"id": "d15ab319-9147-42ed-be5c-3a373ca78852",
		"address_line_1": "addresLine1",
		"address_line_2": null,
		"postcode": "AA1 2DD",
		"city": "Cty",
		"region": "reg",
		"country": "UK"
	}
}
</pre>
sample POST /organisations/sites/ response:
<pre>
{
  "site": {
    "id": "433b8cd8-b1c9-4eb1-a4df-9b5099061950",
    "name": "Test Site 2",
    "organisation": "71f3da6b-7b89-4ffc-9d60-a17f8036f331"
  }
}
</pre>

### Queues
**Queues DTO Structure**
<br> Last Updated 14/5/2019
<pre>
{
    "id":[UUID]
    "name":[free text] 
    "cases":{
        "id":[UUID]
        "application": {
               ...
        }
     }   
}
</pre>

Endpoints for retrieving, creating and updating queues.
<table>
    <tr>
        <th>Method</th><th>URL</th><th>Header</th><th>Body</th><th>Response <br> Codes</th><th>Details</th>
    </tr>
    <!–– Queues ––>
    <tr>
        <td>GET</td>
        <td>/queues/</td>
        <td>?</td>
        <td>None</td>
        <td>200</td>
        <td>Returns all queues</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/queues/{id}</td>
        <td>?</td>
        <td>None</td>
        <td>200 <br> 422 </td>
        <td>Returns a specific queue</td>
    </tr>
</table>

sample GET /queues/ response
<pre>
{
  "status": "success",
  "queues": [
    {
      "id": "00000000-0000-0000-0000-000000000001",
      "name": "New Cases",
      "cases": [
        {
          "id": "eb183b02-71ad-47db-a9ef-0bbf6ffcc665",
          "application": {
            "id": "7ece1b1d-453c-440b-b877-1e337c66839a",
            "name": "First sample draft",
            "activity": null,
            "destination": null,
            "usage": null,
            "goods": [],
            "created_at": "2019-05-15T14:34:55Z",
            "last_modified_at": "2019-05-15T14:34:55Z",
            "submitted_at": "2019-05-15T14:34:55Z",
            "status": "submitted"
          }
        }
      ]
    }
  ]
}
</pre>
sample GET /queues/00000000-0000-0000-0000-000000000001 response
<pre>
{
  "status": "success",
  "queue": {
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "New Cases",
    "cases": [
      {
        "id": "eb183b02-71ad-47db-a9ef-0bbf6ffcc665",
        "application": {
          "id": "7ece1b1d-453c-440b-b877-1e337c66839a",
          "name": "First sample draft",
          "activity": null,
          "destination": null,
          "usage": null,
          "goods": [],
          "created_at": "2019-05-15T14:34:55Z",
          "last_modified_at": "2019-05-15T14:34:55Z",
          "submitted_at": "2019-05-15T14:34:55Z",
          "status": "submitted"
        }
      }
    ]
  }
}
</pre>

### Users
**Queues DTO Structure**
<br> Last Updated 14/5/2019
<pre>
{             
    "email":[valid email address] 
    "password":[free text] 
    "organisation":[foreign key]           
}
</pre>
Endpoints for retrieving, creating and updating users.
<table>
    <tr>
        <th>Method</th><th>URL</th><th>Header</th><th>Body</th><th>Response <br> Codes</th><th>Details</th>
    </tr>
    <!–– Users ––>
    <tr>
        <td>POST</td>
        <td>/users/</td>
        <td>?</td>
        <td>Request:  DTO Structure
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a user </td>
    </tr>
</table>
