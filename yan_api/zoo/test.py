{
  "from": 2,
  "size": 40,
  "sort": {"full_name": "asc"},
  "query": {
      "match": {
          "full_name": {
              "query": query,
              "fuzziness": "auto"
          }
      }
  }
}
