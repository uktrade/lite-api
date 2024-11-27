@db
Feature: units Table

Scenario: Units endpoint
    Given endpoint exists for exporting `units`
    Then the `units` table should contain the following rows:
        | code | description      |
        | NAR  | Items            |
        | TON  | Tonnes           |
        | KGM  | Kilograms        |
        | GRM  | Grams            |
        | MGM  | Milligrams       |
        | MCG  | Micrograms       |
        | MTR  | Metres           |
        | MTK  | Square metres    |
        | MTQ  | Cubic metres     |
        | LTR  | Litres           |
        | MLT  | Millilitres      |
        | MCL  | Microlitres      |
