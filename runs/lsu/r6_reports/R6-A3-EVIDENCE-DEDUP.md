# R6-A3 证据去重清单

按每条 prop_evt 流的内容 SHA-256 去重；同一内容只计一次。

| 内容 SHA-256 | 首次出现 | 重复出现 |
|---|---|---|
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A04-F2-W3 s3 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A04-F2-W0 s1 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A04-F2-W0 s3 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A05-F2-W3 s1 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A05-F2-W3 s2 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A05-F2-W3 s3 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A06-F2-W3 s3 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A06-F2-W5 s3 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A08-F2-W3 s1 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A08-F2-W3 s2 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A08-F2-W3 s3 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A08-F2-W5 s1 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A08-F2-W5 s2 |
| `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` | A04-F2-W3 s1 | A08-F2-W5 s3 |

唯一流 70 条，重复 14 条。
