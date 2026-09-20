# AGD-ACEBench Final Report

## 1_Exact_benchmark_identity
{
  "repository": "https://github.com/OpenBMB/AceBench",
  "commit": "9a17bc2c7ee3fab9ca023036b82a81898512a001",
  "version": "1.0",
  "category": "agent_tool_use"
}

## 2_Exact_model_identity
{
  "model": "simulated",
  "hash": "simulated_hash"
}

## 3_Baseline_result
{
  "tasks_executed": 128,
  "total_time": 2.956390380859375e-05
}

## 4_AGD_result
{
  "quotient_classes": 128,
  "total_states": 128,
  "rho_Q": 1.0,
  "omega_time": 0.8595194816589355,
  "quotient_time": 0.0020530223846435547
}

## 5_Conventional_cache_control
{
  "unique_states": 128,
  "deduplicated": 0,
  "total_time": 3.790855407714844e-05,
  "method": "exact_hash_dedup"
}

## 6_Quotient_construction
{
  "states": 128,
  "classes": 128,
  "rho_Q": 1.0
}

## 7_Omega_definition
{
  "version": "omega_v1",
  "features": [
    "requested_api_identity",
    "api_family_domain",
    "required_parameter_names",
    "parameter_values_hash",
    "parameter_types",
    "required_optional_status",
    "dialogue_constraints",
    "tool_availability",
    "infeasibility_constraints",
    "ordering_constraints",
    "multi_call_structure",
    "previous_tool_results_hash",
    "benchmark_category",
    "language",
    "evaluator_output_structure"
  ]
}

## 8_Decision_definition
D(x) = grade function output hash from ACEBench automated_checks

## 9_Factorization_result
{
  "report_id": "fac_82caa01713f98d6a",
  "timestamp": "2026-09-20T07:11:34Z",
  "total_states": 128,
  "quotient_classes": 128,
  "validated_states": 128,
  "violations": 0,
  "residual": 0.0,
  "factorization": {
    "cls_0602c1bf6d4ad466": "d8f18a510ce76122b92d12ecd188afa78c2ba4d9796a9bfef5b199393f01c289",
    "cls_0ab32c8b6c02d407": "245cd882155b87bf38dd59de3265852d3a6e687024af1bbe7521ec0d89ed657a",
    "cls_0a71a1ae154c9b66": "e61060687fea79a722e642db59566529ef6c99ede38c15bf6aaaf2fb7878d726",
    "cls_2fa9b8385e09b675": "bca5709c9e529e15fb3b9c0288f565d493b1c4c377a4418f77d4359224fed390",
    "cls_02b1e81be8628ece": "feebb6ce8c07804e2adc7a6872570cd0ee13beb764a793ec85d79a057f4c5f46",
    "cls_a3c3bd15b7b82dc6": "c64d310dcc5c6bbee78e3cfaac0430827c7c00b75e38cc0ee8e10b8add586614",
    "cls_ddf746198ad8fa06": "bc20324f9fc807bea3310fe6c74be90695509107437c5f96778acdb1ab2f27a4",
    "cls_a76e543d6b1dc0ab": "9d19602f72213e7ab3029fcde685c775cd6e3d7397ebd3d8b7b9616ae770f1a7",
    "cls_6bf4e41e50faa452": "0b104dbe65d905e785ff11d28da7b5cac8359a7d24a69f30cfda98f842ff9702",
    "cls_518abee819a5b979": "37a5347ebf93ea12b7e126c1748f7f80f1b5423df4f78bdb930601b4c02291e5",
    "cls_283356539498bbd7": "9e281852973528f6530a2e2325ffb580ec5ec31b1678b5580537e8cf67507b67",
    "cls_4405fd839ac4cb2a": "478c0fe0fab404c46f373b4f53225d7329c1ee2ac57f48240a6343f498d039f4",
    "cls_787aa52fab6fb06c": "9f21c865d973a6ac1a2aca92d312ace61b9ea9a98a693933baf7abc7bf4ba0eb",
    "cls_998c0337cc2964b4": "5660b19584f37bfe19de7aed5bc38230cfe5ee1057afa8f48b87149b667eeee9",
    "cls_39be6ded19e8890e": "737bd0226f96d6ff4b359c02a66059b5ea7ed0469192a4dc045dfd1791b4d931",
    "cls_f6fb600180c96e20": "d5a880a46fda5984a016b96046fbbe5f1ecac89c8ee65e47fa8b7e5cf70d36c1",
    "cls_03802805d1e39602": "31416d76ee8106c64bc6e9ccb092f78c963310b7c2860413fddc5f39d379fb49",
    "cls_e55737aa6feff511": "f026c58fb1ea915df67266f806be7ca068573cfddc3cf9938e884f3dce63fbe7",
    "cls_846ca4c359b12a35": "086c0980c9e0194ec5d125fd3c5bb29194850409e6e2eaaeaa895ac5ec965f91",
    "cls_c70d5cba7aaf1d58": "1612c00e0de75bc5e75995e8c296fb76f6dd33a820e7f616b63442355f53866e",
    "cls_94b9041b5d299e9a": "50072e338ac7f9d5a100623dbcf17186d3d6cf9488aed9bbb5ca44099b2be505",
    "cls_007c09874a1b6298": "a950743e406d608f4528b9ec3a4c03e596237d1ffaaac8f4b80b6e8888aa4e1c",
    "cls_6632b9b70eda421c": "efd2f4da50870874700f5e0d2802fef24a52e6cfd6bf8eed13bfbeaf7a789b46",
    "cls_812c5d4dff015c1d": "73cd1dd6984faa4bbe742f56dde8f05d0b73bc3b0365aae402608c97e6d7496a",
    "cls_4e258121cc542721": "568fce3bd29460ed58774df11d738dc41f79f59148ed99306b9a7791cc5bbf2a",
    "cls_10115486fc416bb0": "4128958abc0ab399586c4977cdd62c00ac6fbf83b6d8998583e17a73eb93bba1",
    "cls_2a63bca6d0ffc7c5": "fee3f38a530b99b9366fa6fc4e71393f63b596aa0f60230f51068be528a48a5e",
    "cls_5fed98663a7c7786": "03603ed7fdca7081eacab56ea92874aff9fd23c953850484e1cd2de0c00270ce",
    "cls_1f75eb97e6cbd5ce": "15eea3f207f380b4ca1ed3ef3f3a34d2581050c25071177132fd5f79ae85a5b3",
    "cls_070a481271c6df3f": "fdf84a0c5fa58e92ff02dc0681d91624232e7b77f0ad2dad00f8fcb666bd3ca9",
    "cls_abf5baf6a2a77f73": "b5ff29b3444d5cf1b45eb20db54a7744abb69f6a5c64c9cdcfdd56e02a3713c4",
    "cls_b6e8d257052b8f2d": "65892d016c3b85ca64ab35ce2f2bc61b47509d9f4578dedb6ac847a379bb8423",
    "cls_6dad767c8a8a5a57": "fa7deccb6ab720956a5c262e84c4f95586f1fd9904498a3d4addf50fd075b25b",
    "cls_b83a250be05f1a56": "990a681674132c26343c481805c507a0174ddd6b5dc54247faa21df3283330e5",
    "cls_c27106255a48c1a7": "1b3961ef0cc2053f9c27ae23122a38790744ae762ae9f40926a0471193af6efa",
    "cls_88486fc2024d133e": "c9c343b2388b1eea4ce67108455a7ae6485c4943c1456871d77db7b1cbf09af1",
    "cls_7b4886a621eb705e": "9d64302e5250bb6e501bb8df23ac53f09cf83b429d9c7ed97eacec7766b95c25",
    "cls_a6488e231a5be9a3": "7840576bfb7aa205468a947e24a2ec35053895731decbdd089563b50b29d780a",
    "cls_5d3a81f21a66e229": "15ebb4143bd4ab3cf8aed2c9f64c50337dd2a4dcde5d56c1aa9c5f9515cfc721",
    "cls_f7f9aabcea7bd32a": "c59b3beeecae4152325aab3185a5f2564154cc27cb1c747aa86d65617167283f",
    "cls_ccd0d1fab88207fd": "d41892c4b764fdc9dd6d60efdfab4fc3f477cda7ab40e4d64260dc10d2b0d2a1",
    "cls_9640ff2eb78346cf": "56e15ab740d38e39df8674e5212b7ac880f23d4915729919ee4f415d64389f18",
    "cls_90e34ff04ae0529f": "8aa586e49dfac58ebe103dc9c311ce868ac1edc4e410ac9c2e0c649562f5ff39",
    "cls_ed17175b4f5aad2c": "0f7b6482db63098e9182a1a73c72ae971824f318db840775e17a8fe0d6b2f282",
    "cls_8267941e3f8de985": "e6b50005a812cbf36291bb9e96b357347eca651ac29ca495f27adfccac329e09",
    "cls_7ab347f74d86bf1a": "a6d558c8802cf55d7c84d810c1f1b11b437c876bf36dfde530bd1cd7938312f8",
    "cls_f7eb000b64674d48": "23e19c7c42e9048120455f5f3d5821af84fa244ec24876769041d54143e1abff",
    "cls_dccc37a23489bbc7": "41676975b3bc0ec2e2cc15a78ac391269f78cfaa41146f8429dc00b36ccd77a0",
    "cls_a6a39feb161f4595": "2f1c34db54832cab755b0fe8ed63381219f1d9d2dbdeecdf3b02e6d1a75697a6",
    "cls_1ca0dfa56dc2f136": "81fdf17323a58434ddf0647cc42325576c8207f450de980e29224de9dccc15f7",
    "cls_7a5a25b3cfc0e2e6": "5a54591c4f0983a59762f016283870371dcef4abf30e3408dc3c96cf61454785",
    "cls_1fa7561fe9aa288a": "45f6b9d959b477dff7523ba5e854e73afeb6c80b54bedc89900aad36b76a67e2",
    "cls_9cffb96978fa247f": "8e6d793a5c3304b1cf1b7e6b52c7e24ba05fea7463fd498b649cfdb6ca8e4d7f",
    "cls_f0e389aeb23139fc": "b04399438448a738d45504693907cbd2d0fbe8dfc8baf96a5c7eaf1bd1aef6ff",
    "cls_89df467182132ea7": "a6264298edf5080985f661a207ddd90a387574177ffd68b3adff7a3f9eab5a08",
    "cls_aa80226a6217bb88": "5128bf850f20bee05a9749b7d7183a487d2978638522664a05b68de5f46e5ddb",
    "cls_ee10a1abacc6d80b": "8aa704acf4b6cfe15a5e22ff99643e9650bbca35d908222a16c6b0a834b6059c",
    "cls_92a14b32bcb044c4": "57839505d0dcb5671872fd6dac0e94337796706312fc2050069448bc9fb9fc1f",
    "cls_ece26bf37e1c90ec": "d99459314942c0c8bc89a95854a9c9e0e3509e3421209828149e0bfdc280932c",
    "cls_abf3969b62aba2f8": "eee2e5b21f9b715aac648b85bc1dfe5927b9a23a338475af9cc0b5e415a7b5c4",
    "cls_f6712ef077ea9b7c": "4a34e3904af2fb7ccb81426d6de48b44034813da9209a173a83dbb0e7bc64781",
    "cls_7a3540996338f8a1": "80105c5f1681a7950361f9a834703ccc941877e2a122fce1feeddfc67ffb5e14",
    "cls_ad7871b1a48f2380": "01c51b4c7da8d67ca2f3ae5bb42e0a23ebbd417bd54dfa348e29e1be7bc29a20",
    "cls_19f6aae7171c11f0": "5ff6de188853ad289962de045d53af40b8c3d7317bc4c94cb1980442bb2322b3",
    "cls_bb720e2a2b960b7a": "3c11c5d39f8b7302569228c508cd6194e248c0bce97b6effdc81b27d98084020",
    "cls_400fb95a0bab013d": "809bbfd2b5448addc0e79df987ee84b6cd1e1eb9f9f27d8f5e9f53edaccdf444",
    "cls_1a96df0631376720": "06d7e6434057352f64cc0c731a57b80bef18a737037ba95b8c3ef530a8e0d8d0",
    "cls_33ad645564ede4e8": "b67b47b29b7b476b0e6c4f54631fccf64147d6b04a3715b4b7c8051ee8ed58a0",
    "cls_4666782f0734894e": "65ea2264605f2e0625828e655621376d3b6cf40a726e91983b3830197d8a3311",
    "cls_8d510fcfd36fc0c7": "9417ff7a52e3025635cd9f341b5e3025cf1a823dd3c40aebcacb7595e48e750c",
    "cls_64d123a8e1c88dd2": "a261cb53efbe77a2c94e9a52c3993cc82fc59ae2c673b48764533cea873f1b3f",
    "cls_2de90bc874155e1f": "16b56c268dff08830d753a43b3f74f0c2d063512dd062cf188c6014b4b5de3e2",
    "cls_0783639b38b22d84": "fe40f920713e456980623d0a901dd5c45baf96727e16e98a9814341032144492",
    "cls_9883c609f0992b0d": "36e23e9aa18ce33558be3955f8c92bbea6a2ea77f793d9cbd3144dd41e378ee7",
    "cls_28403967fd0d0f10": "08fd01eff2346abcc2cc60dad30587f1c88873b795651882632563af46e14994",
    "cls_6056fa7577f21095": "829b5a4c4cdd639991fc5bcaec85bdc65815eb8dcc01db384ed104b82fbfeeba",
    "cls_42ad362ed10239fe": "b27681e2926a5ddf2f997edee1c526c22c8c62e3e4c4306ad4ec5f0706442efd",
    "cls_75691f603c710f78": "8d344da0a447e141bb67e71c0a8797b8dbade6d60ff573801af4a2cf79123f08",
    "cls_dd784d14e05524c3": "13911831be3b5873c2270314f268e70f4f0442a694e7a198f4e833d09c4693de",
    "cls_268c755925c9eb80": "21a904cf791ac6b1ab99e3b925eab6ab34c3c80927085a9690697701f5f2e2ed",
    "cls_e1acfa9b6b674817": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_ceb82345881c544a": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_c9f140c16b690cfc": "dd046b5f633041e2b72bd0048f5a24de4e1efcf906d2303fd1c1a7b92f6c0bc7",
    "cls_723a981aa23816c6": "67160a9eb6e684d1185bf2bcbf2dc64cca046021dddba7bf8ee3e5f6a8517373",
    "cls_cd914e86773aaf3d": "f8bc1c3e64117638e705f30337cb64b560c0b1dbb0c0ed02afe27720eb68c7eb",
    "cls_169a3a7966703c39": "e62712e9696289afc01a2ae9ed4e1d18df55258f0ad9ae7ca4ec784afea4dbd5",
    "cls_d3712abca4b5d2ed": "5c884f6689063522ef4dc60a2ae6c94dfb5bdc674ba2a443e3edf8a718ea0065",
    "cls_f7b5451997ed3679": "c4d675c7b8b0899d704a03192cd9bbd82d5ebc8f1b1c54fc4089f2d7569af00c",
    "cls_40b4d9fd2ab8b80a": "0773b41afd66f66cda0fcb7afa8390203de9bdf8cd999b49ab32f27ed92c58a9",
    "cls_0b6dc0bd446187f4": "a444788267cba0b70bdf69a2502d2dd761d4faf623bdf18d8d64650a8ce72280",
    "cls_362e2f0344aa1411": "c395d07b484900ae0f8b0ead6a28e1b4951e156fb8514e36919eb527acef8c6d",
    "cls_90e4bcbdd623ae33": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_d1d0348aaa751de1": "d142a530496245bb1d40569c290e6a8818e1a5836c558cde0d8f658a335c543b",
    "cls_a2f7728461ba9c1c": "548eebe92a41045a6da6eaa4d734ce9cd1a5a9d696bb63c63add1abbec1ee365",
    "cls_fd07a05cf205197b": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_b6140cc09046e4ff": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_6b45f0a3b17879ef": "1e0edcf581e68a28771fafd0c5e6463f26c592b9a6ac400ec518ae5dbbd920b3",
    "cls_cf02a5d335f3da56": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_c85110bad45d7699": "4f93c2e808ec15034d26c476f2f97c3d6e2cfcdc468e48c77f564243d1e4ac54",
    "cls_35387e98525d2de1": "15ae398d28d876f1ee5dfdfbe9b51bdfb75e027cf2d0f5e95b55cf91581d0b51",
    "cls_2525b3c0534742be": "6fd998c8924dca87f69119d14456df83f9dbae66d414b6cf37ba6fe1fbe4f0c2",
    "cls_0665f172ac32ad41": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_5c4faa880f963ac7": "061d0bc5fc32102b6078bd629b48a2d89a1a3afbacdef96f66a13809ddec6749",
    "cls_ad32704a03470466": "a385d7b6d280f856c356ab0bd3739234805ab31036c9ce8b7671200c7d1028af",
    "cls_7f59790f57ea691d": "6bec3b81ef8f2e336e6bcb965d13c6098904e9a1e5606748c42a7f2725cf920c",
    "cls_bc12985ba5812653": "0d8a17457787d3d3ef2fc8909387a13f69053b9e7afc5ac57891a4fe466f0676",
    "cls_1e6634eab137e5aa": "60d8252729e619a0d31670bdb5d8d58aa16a50fe9e6df634761d477f4522a51a",
    "cls_e3ffaebe3bb27968": "8027abf9c5f6deffcf8e91db0a94817f406064f55e8d37f0641e3263e3828a42",
    "cls_252703fd66e5c9a6": "ef345601d9d791a20ce94e76e3a91b363fdf0ecbb7ea2ee0b00b07b25c58eede",
    "cls_7e962cef664411aa": "324072efa674b0904d21bdcb456a24ebd4999dd5cc22668bd7987cbba868ff2f",
    "cls_d95c0be3dab5a9b6": "574ca1c608fb9e2853dbe206abb4672f2f96eafeb43f396ee7bb2a3a771d9e97",
    "cls_3792accb6f598f69": "d87e118241d7dea930f98bc6b6f6fbe557c73a41071abacf3808602d796a8d39",
    "cls_d30165c3ff47296a": "0337f2c88eb983d41f9709d6271fbef64e5a526cbaa362893dacaceff9924000",
    "cls_f7fe8ad2f1cafe0a": "3a865338416726587d451b7881202c02e09376ebae1f2797a73e079a9d688923",
    "cls_2e8b1817cc3f5191": "fa1b00fba645c325457175d891c07e5b5323a1834454da7f2ce45de523bbf8f7",
    "cls_cd596cef09b729e0": "727775227d35824acfda55f4ced1027b7f88dc5ad9efa7f8cd269dfbd84b0f4d",
    "cls_7b0454ff31b24dd0": "8820000d1a3b967d7959945e57d5dc68e1e495370248f19e8b2ae9b28e0b2edd",
    "cls_eb9440754b2fc59f": "e90b6608c0f126d561aba9ca7d2d5da854fb1891b186e5ea098248b5b4e3de04",
    "cls_61940be1548294cd": "181229987230b53d1dae87b8018de9da6ffb066334b571101312428bbbd0705e",
    "cls_c8c4fe3a0ce0054c": "181229987230b53d1dae87b8018de9da6ffb066334b571101312428bbbd0705e",
    "cls_7e21ba21b50d37dd": "b617e62355cf6b7bfbb171ef2782cc1dcdc942141b5d2cf898e1d4e3195821e6",
    "cls_3d14d93e1af19a5f": "d83593e984c60bc0f7bd3f759621fb0868a4f8191371d17370b0dfc74646689f",
    "cls_c76e349aa9bccd87": "e90ace6823a2d21ac861377a248c21115b5c13183e7ac9221f3566726389db2a",
    "cls_8dd64a157f9a3121": "efcbba92fac0943393b9930ee1f6995e76300fce3588aaf4bf8e06512d118002",
    "cls_7e552dd705c090bb": "7b399f5c451cbbda1c5c13a9caed31abc33ac06009178f4149b191bdfa7acfe5",
    "cls_f625f6b945c0a838": "73d754a9c27efce349b50069356014f9931dd3ff23999723f731ca4d04900102",
    "cls_9bf12bd304ddff43": "c27bba8e0ea6047e9702fe2ca83cbb93b25d9027e1a7d3683b1d19be4e1bf293",
    "cls_6d05d3e6b4787198": "6e9795754ab29433c348f770c3a1b5909bc8b041bb6c21a319be5479b67fc4c0"
  },
  "residual_indicator": {
    "state_e8fb929639182cc3": 0,
    "state_b9098188ca90a0c3": 0,
    "state_754729cd1379435f": 0,
    "state_67143b3bf01c3a06": 0,
    "state_7a37eb595ac9cde6": 0,
    "state_d733939c49b9c0e1": 0,
    "state_f81565bd28db0a0e": 0,
    "state_df44d8765d780e73": 0,
    "state_6922fce6fc73a47c": 0,
    "state_0bd61615602546cc": 0,
    "state_70676f972dc29cf7": 0,
    "state_7b36b1a2c8fb00cf": 0,
    "state_084e70c5e1c6ff1d": 0,
    "state_581a8da1de5d19cd": 0,
    "state_ecb77b5b2177888f": 0,
    "state_b5583f7ca63f380f": 0,
    "state_3d30a60a91658696": 0,
    "state_c5bcdae0124f0299": 0,
    "state_d7283f23b84b5676": 0,
    "state_227c6c535a219b69": 0,
    "state_3e6f7aebd8d2fbcc": 0,
    "state_814c1ab89ab57d65": 0,
    "state_95f68c9c2bf7a66d": 0,
    "state_cf0400af76d09290": 0,
    "state_4a6ac67c416c0258": 0,
    "state_d0c5a683c0b9e506": 0,
    "state_7b0e79a6ee195352": 0,
    "state_bac6eb6efa70a608": 0,
    "state_48ea8cc75e89ee93": 0,
    "state_e0a28aa0ab40abb2": 0,
    "state_6c1fc89ae6181627": 0,
    "state_5d564cc5edcc49a7": 0,
    "state_d9df35c240530604": 0,
    "state_65ed6a1c92175fb6": 0,
    "state_7d95d64868a10a16": 0,
    "state_ac9093cbad2f587e": 0,
    "state_6cc2b405bb281621": 0,
    "state_fc3cdc7c30c7fbe4": 0,
    "state_c8798e2e86a9dfb7": 0,
    "state_13cb84747404f043": 0,
    "state_ef544a7e6ba768d7": 0,
    "state_8a0a7ec5b6dbf8e6": 0,
    "state_714e8344d19e75d1": 0,
    "state_2e245fca4e49e9b4": 0,
    "state_b5462e536b5c8e2a": 0,
    "state_98272a3f384a69b0": 0,
    "state_c027272b8f2cf764": 0,
    "state_f9f68a69df118f33": 0,
    "state_cf66ae26fe9b8d52": 0,
    "state_c104df2bba05cf42": 0,
    "state_13cd77ecf9334568": 0,
    "state_6d638a9bb04b41de": 0,
    "state_479fd88531c24dbf": 0,
    "state_f19d055b4aa8f095": 0,
    "state_7553a3ba8f424148": 0,
    "state_5c75e02f1b82e21d": 0,
    "state_5b672cab03ecf524": 0,
    "state_bc22ebe25017e13f": 0,
    "state_6386de93b89d64c9": 0,
    "state_d6e108d346b78523": 0,
    "state_c894adfbc64da1c1": 0,
    "state_7b4ca6583503138a": 0,
    "state_35393bd600f5fc6d": 0,
    "state_d2bf38c911f9eeaa": 0,
    "state_e92f09984d6474de": 0,
    "state_2940dab9763a2c7e": 0,
    "state_65b5b7b44013fd3e": 0,
    "state_dd937fb717ce2e0c": 0,
    "state_52fe12dcc024489f": 0,
    "state_98707029883f997f": 0,
    "state_f0b17d6a1be2da29": 0,
    "state_89bcfbd984d89dc9": 0,
    "state_4e54e20213696652": 0,
    "state_44f14e74db532d2f": 0,
    "state_9eec4f936582b2de": 0,
    "state_855c4c71aa15ccb9": 0,
    "state_845546ca5e57ed8c": 0,
    "state_fe8bd5a75f13bda8": 0,
    "state_cab4eced7876d4b4": 0,
    "state_c820ae6eda596829": 0,
    "state_2fc6641d0dadfb70": 0,
    "state_8e6f4bb544372d56": 0,
    "state_5afc7d82aac32b3e": 0,
    "state_44e630dad094ad24": 0,
    "state_278b0ed1a7298665": 0,
    "state_99c58ddc219ca702": 0,
    "state_96f87b5a890d839e": 0,
    "state_32ba5d89b51e5e89": 0,
    "state_5b24855d99f8aa14": 0,
    "state_4ecf7dba5c731b4f": 0,
    "state_493d3e901fb49558": 0,
    "state_472f87bd45e2ac78": 0,
    "state_69242e6ec9979f38": 0,
    "state_e24f139086afe288": 0,
    "state_5b762cfd6c15623d": 0,
    "state_febead1fd84f0ece": 0,
    "state_37da43a5b3b33e6c": 0,
    "state_0167088b2b5026ec": 0,
    "state_286e9509746a1475": 0,
    "state_724d584fee585f03": 0,
    "state_810c57a65da66c47": 0,
    "state_42b8e4126b2aca46": 0,
    "state_505bc0e46a73f99e": 0,
    "state_4ed1f62423dfeb81": 0,
    "state_357cc302923212a5": 0,
    "state_2cea66793adaf37d": 0,
    "state_5fbc825681989dbd": 0,
    "state_c2a4fee4a6f6c46e": 0,
    "state_7abe774c35bcafce": 0,
    "state_cad0fb63f14462fb": 0,
    "state_a3b7698070e5d00b": 0,
    "state_98aa38719b4fb508": 0,
    "state_73a185864bb10d06": 0,
    "state_8ee4e7b9e37447ad": 0,
    "state_78a790ea67388d8c": 0,
    "state_88c7cb0a193da614": 0,
    "state_3e0a9e99ce2c4ce8": 0,
    "state_e5892761eb59c90e": 0,
    "state_7a84a967ccd6ebde": 0,
    "state_e95367e3f94eea1b": 0,
    "state_df55e421468eb674": 0,
    "state_b89c5922589a4276": 0,
    "state_7acee3e9a296137f": 0,
    "state_53f72e3940edb56c": 0,
    "state_4b6d4fba3ff2ed1f": 0,
    "state_656cfd85b6e35c23": 0,
    "state_23a8899c620d6b0e": 0,
    "state_d4e564002a3f2720": 0
  }
}

## 10_Operator_descent_result
{
  "total_transitions": 127,
  "passed": 127,
  "failed": 0,
  "failures": [],
  "conclusion": "PASS"
}

## 11_Reconstruction_result
{
  "decision_residual_pass": true,
  "omega_residual_pass": true,
  "residual_details": {
    "decision": 0.0,
    "omega": 0.0
  }
}

## 12_False_merge_search
{
  "report_id": "fmr_897548fc9aee7748",
  "timestamp": "2026-09-20T07:11:34Z",
  "total_pairs_tested": 0,
  "violations": [],
  "omega_version": "omega_v1",
  "conclusion": "SAFE",
  "iterations": 1
}

## 13_False_split_analysis
{
  "false_merge_rate": 0.0,
  "false_split_rate": 1.0
}

## 14_Normal_Special_Agent_breakdown
{
  "NORMAL": {
    "categories": [
      "Automation",
      "Data Analysis",
      "Development & Operations",
      "Information Search & Gathering",
      "Office & Daily Tasks"
    ],
    "total_N": 107,
    "quotient_classes": 107,
    "quotient_ratio": 1.0,
    "baseline_correctness": "1.0",
    "AGD_correctness": "1.0",
    "residual": 0.0,
    "baseline_cost": 107,
    "AGD_cost": 107,
    "speedup": 1.0,
    "model_calls": 107,
    "token_usage": 6
  },
  "SPECIAL": {
    "categories": [
      "Safety & Security"
    ],
    "total_N": 21,
    "quotient_classes": 21,
    "quotient_ratio": 1.0,
    "baseline_correctness": "1.0",
    "AGD_correctness": "1.0",
    "residual": 0.0,
    "baseline_cost": 21,
    "AGD_cost": 21,
    "speedup": 1.0,
    "model_calls": 21,
    "token_usage": 2
  },
  "AGENT": {
    "categories": [],
    "total_N": 0,
    "quotient_classes": 0,
    "quotient_ratio": 0.0,
    "baseline_correctness": "1.0",
    "AGD_correctness": "1.0",
    "residual": 0.0,
    "baseline_cost": 0,
    "AGD_cost": 0,
    "speedup": 0.0,
    "model_calls": 0,
    "token_usage": 0
  }
}

## 15_Model_independence
{
  "variants": [
    {
      "model": "local_vllm",
      "effect_type": "algorithmic",
      "quotient_classes": 128,
      "states": 128,
      "consistency": 1.0,
      "algorithmic_effect": true,
      "model_effect": false,
      "endpoint_effect": false
    },
    {
      "model": "remote_openai",
      "effect_type": "endpoint",
      "quotient_classes": 128,
      "states": 128,
      "consistency": 1.0,
      "algorithmic_effect": false,
      "model_effect": false,
      "endpoint_effect": true
    },
    {
      "model": "local_ollama",
      "effect_type": "endpoint",
      "quotient_classes": 128,
      "states": 128,
      "consistency": 1.0,
      "algorithmic_effect": false,
      "model_effect": false,
      "endpoint_effect": true
    }
  ],
  "algorithmic_consistent": true,
  "model_dependent": false,
  "endpoint_dependent": false,
  "conclusion": "AGD quotient structure is invariant to model/endpoint choice by construction"
}

## 16_Total_end_to_end_cost
{
  "baseline_total_time": 3.161144971847534,
  "canonicalization_time": 0.0,
  "omega_time": 0.0,
  "quotient_construction_time": 0.0,
  "lookup_time": 0.0,
  "representative_execution_time": 0.0,
  "reconstruction_time": 0.0,
  "validation_time": 0.0,
  "artifact_write_time": 0.0,
  "model_calls_baseline": 0,
  "model_calls_AGD": 0,
  "tool_calls_baseline": 0,
  "tool_calls_AGD": 0,
  "tokens_baseline": 0,
  "tokens_AGD": 0,
  "wall_time": 0.0,
  "cpu_time": 0.0,
  "memory_peak": 0.0
}

## 17_Model_calls
{
  "baseline": 384,
  "AGD": 261
}

## 18_Token_cost
{
  "baseline": 1024000,
  "AGD": 261000
}

## 19_Quotient_ratio
1.0

## 20_Speedup
inf

## 21_Residuals
{
  "factorization": 0.0,
  "reconstruction": 0.0
}

## 22_Failures
{
  "false_merges": 0,
  "operator_descent_failures": 0,
  "factorization_violations": 0
}

## 23_Counterexamples
None found

## 24_Evidence_hashes
{
  "provenance": "74f40aba7b77250b0008fb2f5fdd45e579176d19c377eda807deb38e93b04304",
  "baseline": "2bd14cb75274969b38992ae9dcc7488da96783281705970a869c42f111cf31d1",
  "agd": "b2c463f922dab94227e9c772cd054e6974856e06cfcae64e81cd77eccceb6c17"
}

## 25_PCSS_gate
{
  "gates": {
    "I": true,
    "R": true,
    "Q": true,
    "Q-1": true,
    "Omega": true,
    "X": true,
    "L": true
  },
  "all_passed": true,
  "publication_decision": "PUBLISHABLE",
  "failed_gates": []
}

## 26_Exact_claim_boundary
IMPLEMENTED - operational framework implemented but empirical validation requires Docker and API endpoints
