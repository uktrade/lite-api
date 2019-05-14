## API Reference

### Applications

**Application DTO Structure**
<br> Last Updated 14/5/2019
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
        <td>POST</td>
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


### Drafts
**Draft DTO Structure**
<br> Last Updated 14/5/2019
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

### Organisations
**Organisation DTO Structure**
<br> (Might Need Updating)
<pre>
{
    "id":[UUID]
    "name":[free text]
    "eori_number":[free text], 
    "sic_number":[free text],
    "vat_number":[free text],
    "registration_number":[free text],
    "address":[free text],
    "admin_user_email":[valid email address]            
}
</pre>


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

### Sites
**Sites DTO Structure**
<br> Last Updated 14/5/2019
<pre>
{
    "name":[free text]
        "address":{
           'address_line_1':[free text],
           'address_line_2':[free text],
           'postcode':[free text],
           'city':[free text],
           'region':[free text],
           'country':[free text]
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
        <td>/sites/</td>
        <td>?</td>
        <td>Request:  None <br> Response: List of DTOs </td>
        <td>200</td>
        <td>Returns all sites belonging  <br>
         to the users organisation</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/sites/{id}</td>
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

### Queues
**Queues DTO Structure**
<br> Last Updated 14/5/2019
<pre>
{
    "id":[UUID]
    "name":[free text] 
    "cases":{
        "id":[UUID]
        "application" : {
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