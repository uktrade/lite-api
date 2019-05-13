## API Reference

### Applications

Endpoints for retrieving, creating and updating applications.

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
        <td>None</td>
        <td>200</td>
        <td>Returns all applications</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/applications/{id}/</td>
        <td>?</td>
        <td>{ <br> 
                'id': '12345' <br>  
            }
        </td>
        <td>200 <br> 404 </td>
        <td>returns application with given id</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/applications/</td>
        <td>?</td>
        <td>{ <br> 
                'id': '12345' <br>  
            }
        </td>
        <td>200 <br> 422 </td>
        <td>Requires valid draft id <br>
            Submits application with aforementioned id <br>
        </td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/applications/</td>
        <td>?</td>
        <td>all optional <br>
            { <br>
                "name":[free text]  <br>
                "control_code":[free text]  <br>
                "activity":[free text] <br>
                "usage":[free text] <br>
                "destination":[free text] <br>
                "status":[enum of statuses] <br>
            }
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
        <td>None</td>
        <td>200</td>
        <td>Returns all drafts</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>drafts/{id}/</td>
        <td>?</td>
        <td>None</td>
        <td>200   <br>
            404
        </td>
        <td>returns details of a specific draft</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/drafts/</td>
        <td>?</td>
        <td>{ <br> 
              "user_id":[UUID of user] <br> 
              "name":[free text] <br>  
            }
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a draft </td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/drafts/{id}</td>
        <td>?</td>
        <td>all optional <br>
            { <br>
                "name":[free text]  <br>
                "control_code":[free text]  <br>
                "activity":[free text] <br>
                "usage":[free text] <br>
                "destination":[free text] <br>
            }
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

### Organisations & Sites
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
        <td>None</td>
        <td>200</td>
        <td>Returns all organisations</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/organisations/{id}</td>
        <td>?</td>
        <td>None</td>
        <td>200   <br>
            404
        <td>Returns details of a   <br>
        specific organisation</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/organisations/</td>
        <td>?</td>
        <td>{ <br> 
                "name":[free text] <br>
                "eori_number":[free text], <br>
                "sic_number":[free text] <br>
                "vat_number":[free text] <br>
                "registration_number":[free text] <br>
                "address":[free text] <br>
                "admin_user_email":[valid email address] <br>               
            }
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a organisation </td>
    </tr>
</table>

### Sites
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
        <td>None</td>
        <td>200</td>
        <td>Returns all sites belonging  <br>
         to the users organisation</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/sites/{id}</td>
        <td>?</td>
        <td>None</td>
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
        <td>{ <br> <pre>
                "name":[free text] <br>
                "address":{ <br>
                  &ensp 'address_line_1':[free text], <br>
                  &ensp 'address_line_2':[free text], <br>
                  &ensp 'postcode':[free text], <br>
                  &ensp 'city':[free text], <br>
                  &ensp 'region':[free text], <br>
                  &ensp 'country':[free text] <br>
                  &ensp }  <br>              
            }</pre>
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a organisation </td>
    </tr>

</table>

### Queues
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
        <td>{ <br>            
                "email":[valid email address] <br>
                "password":[free text] <br>
                "organisation":[foreign key] <br>          
            }
        </td>
        <td>200 <br> 422 </td>
        <td>Creates a user </td>
    </tr>
</table>