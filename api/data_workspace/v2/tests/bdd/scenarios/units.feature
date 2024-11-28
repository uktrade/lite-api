@db
Feature: units Table

Scenario: Units endpoint
    Given LITE exports `units` data to DW
    Then the `units` table has the following rows:
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
