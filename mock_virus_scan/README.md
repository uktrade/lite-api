# Mock Virus Scan

The purpose of mock virus scan is to give us the ability to swap out the external third party virus scan services that we use.

Swapping this out is useful when:

  - we are running end-to-end tests and we don't want to rely on external services
  - we want to develop locally without an internet connection

This mock replaces the virus scanning of documents that are uploaded. It's a dummy and not intented to provide any of the functionaity. It supports a postive scan using the ECIR pattern. 

To enable set MOCK_VIRUS_SCAN_ACTIVATE_ENDPOINTS = True