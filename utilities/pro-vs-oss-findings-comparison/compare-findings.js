
const htmlCreator = require('html-creator');

const file1 = process.argv[2];
const file2 = process.argv[3];
const output_file = `findings-compared-${get_now_timestamp()}.html`;

const file1_findings = require(file1);
const file2_findings = require(file2);

const bootstrap_bundle = {
    type: "script",
    attributes: { src: "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" }
}

const html_head = {
    type: "head",
    content: [
        {
            type: "title",
            content: "Semgrep Findings Comparison",
        },
        {
            type: "script",
            attributes: { src: "https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js" }
        },
        {
            type: "script",
            attributes: { src: "https://cdn.datatables.net/v/dt/dt-1.13.7/datatables.min.js" }
        },
        {
            type: "link",
            attributes: {
                rel: "stylesheet",
                href: "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
            }
        },
        {
            type: "link",
            attributes: {
                rel: "stylesheet",
                href: "https://cdn.datatables.net/v/dt/dt-1.13.7/datatables.min.css"
            }
        },
        {
            type: "script",
            content: `$(document).ready( function () { $('.findingsTable').DataTable(); } );`
        },
    ],
}

function get_now_timestamp() {
    return (new Date()).toISOString().slice(0, 19).replace('T','.').replace(/:/g,'.');
}

function get_findings_difference(left_findings, right_findings) {
    const left_only = left_findings.results.reduce((left_only_findings, left_finding) => {
        const is_shared = right_findings.results.some(right_finding => right_finding.extra.fingerprint === left_finding.extra.fingerprint);
    
        if (!is_shared) {
            left_only_findings.push(left_finding)
        }
    
        return left_only_findings;
    },[])

    return left_only;
}

function get_findings_intersection(left_findings, right_findings) {
    const intersection = left_findings.results.filter(left_finding => 
        right_findings.results.some(right_finding => 
            right_finding.extra.fingerprint === left_finding.extra.fingerprint
        )
    );

    return intersection;
}

function generate_findings_table(config) {
    return {
        type: 'div',
        attributes: { class: 'row' },
        content: [
            {
                type: 'div',
                content: config.title,
                attributes: { class: 'h1' }
            },
            {
                type: 'table', 
                attributes: {id: config.id, class: 'findingsTable table table-striped table-hover'},
                content: [
                    { type: 'thead', content: [ 
                        { type: 'tr', content: [
                            {type: 'th', content: "Rule"},
                            {type: 'th', content: "Confidence"},
                            {type: 'th', content: "Severity"},
                            {type: 'th', content: "Path"},
                            {type: 'th', content: "Line"}
                        ]}
                    ]},
                    ...config.findings.map(finding => {
                        return {
                            type: 'tr', content: [
                                {type: 'td', content: finding.check_id},
                                {type: 'td', content: finding.extra.metadata.confidence},
                                {type: 'td', content: finding.extra.severity},
                                {type: 'td', content: finding.path},
                                {type: 'td', content: finding.start.line}
                            ]
                        }
                    })
                ]
            }
        ]
    }
}

const results = {
    file2_only: get_findings_difference(file2_findings, file1_findings),
    both_file_findings: get_findings_intersection(file2_findings, file1_findings),
    file1_only: get_findings_difference(file1_findings, file2_findings)
}

const html = new htmlCreator([
    html_head,
    {
        type: "body",
        attributes: {class: "container"},
        content: [
            generate_findings_table({id: "proOnly", findings: results.file2_only, title: `Findings only in ${file2}`}),
            generate_findings_table({id: "shared", findings: results.both_file_findings, title: 'Findings in both files'}),
            generate_findings_table({id: "ossOnly", findings: results.file1_only, title: `Findings only in ${file1}`}),
            bootstrap_bundle
        ]
    }
  ]).withBoilerplate();

  html.renderHTMLToFile(
    output_file,
    {
      htmlTagAttributes:
      {
        lang: "EN",
      }
    }
  );

